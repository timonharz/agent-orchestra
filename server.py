import os
import ssl
import time
import uuid
import asyncio
from typing import Dict, List, Optional

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
except ImportError as e:
    print(f"Error importing Flask dependencies: {e}")
    print("Please install Flask and Flask-CORS: pip install flask==2.2.3 flask-cors==4.0.0 werkzeug==2.2.3")
    exit(1)

from werkzeug.serving import run_simple

try:
    from app.llm import LLM
    from app.agent.manus import Manus
    from app.agent.toolcall import ToolCallAgent
    from app.schema import Message
except ImportError as e:
    print(f"Error importing application modules: {e}")
    print("Please make sure all requirements are installed: pip install -r requirements.txt")
    exit(1)

app = Flask(__name__)
CORS(app)

# Initialize agent cache
agent_cache = {}

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Agent Orchestra API"})

@app.route("/api/models", methods=["GET"])
def list_models():
    """List available models"""
    models = {
        "models": [
            {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "OpenAI via OpenRouter"},
            {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic via OpenRouter"},
            {"id": "mistral/mistral-large", "name": "Mistral Large", "provider": "Mistral via OpenRouter"},
            {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 Flash", "provider": "Google"}
        ]
    }
    return jsonify(models)

def get_agent_for_model(model_name: str, agent_id: str = None):
    """Get or create an agent for the specified model"""
    config_name = "default"
    if model_name.startswith("anthropic/"):
        config_name = "anthropic"
    elif model_name.startswith("mistral/"):
        config_name = "mistral"
    elif model_name.startswith("google/"):
        config_name = "gemini"

    # Create a unique agent ID if not provided
    if not agent_id:
        agent_id = f"{config_name}-{str(uuid.uuid4())[:8]}"

    # Create a cache key
    cache_key = f"{agent_id}-{model_name}"

    # Return cached agent if exists
    if cache_key in agent_cache:
        return agent_cache[cache_key], cache_key

    # Initialize LLM for the agent
    llm = LLM(config_name=config_name)

    # Create a new agent
    if model_name.endswith("vision"):
        # Vision-capable agent
        agent = ToolCallAgent(
            name=agent_id,
            llm=llm,
            description="Vision-capable agent that can process images and use tools"
        )
    else:
        # Default agent
        agent = Manus(
            name=agent_id,
            llm=llm,
            description="General-purpose agent with tool-using capabilities"
        )

    # Cache the agent
    agent_cache[cache_key] = agent

    return agent, cache_key

@app.route("/api/agent/run", methods=["POST"])
async def run_agent():
    """Process requests through the agent system"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        # Extract request parameters
        model = data.get("model", "openai/gpt-4o")
        messages = data.get("messages", [])
        agent_id = data.get("agent_id")
        task = data.get("task")

        # Convert messages to the format expected by the agent
        formatted_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "user":
                formatted_messages.append(Message.user_message(content))
            elif role == "assistant":
                formatted_messages.append(Message.assistant_message(content))
            elif role == "system":
                formatted_messages.append(Message.system_message(content))

        # Get or create an agent for this request
        agent, cache_key = get_agent_for_model(model, agent_id)

        # Add messages to agent memory
        for msg in formatted_messages:
            agent.memory.add_message(msg)

        # Set task if provided
        if task:
            # Create a response to process through the agent
            response = await agent.process_task(task)
        else:
            # Use the last user message as the task
            last_user_msg = next((msg for msg in reversed(formatted_messages)
                                if isinstance(msg, Message) and msg.role == "user"), None)
            if last_user_msg:
                response = await agent.process_message(last_user_msg.content)
            else:
                return jsonify({"error": "No user message or task provided"}), 400

        # Format response
        result = {
            "id": f"agent-{str(uuid.uuid4())}",
            "agent_id": agent.name,
            "created": int(time.time()),
            "model": model,
            "response": response,
            "messages": agent.memory.get_messages_as_dict(),
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat/completions", methods=["POST"])
async def chat_completions():
    """Legacy chat completion API endpoint"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        # Extract request parameters
        model = data.get("model", "openai/gpt-4o")
        messages = data.get("messages", [])
        temperature = data.get("temperature", 0.7)

        # For compatibility, get a simple LLM instance
        config_name = "default"
        if model.startswith("anthropic/"):
            config_name = "anthropic"
        elif model.startswith("mistral/"):
            config_name = "mistral"
        elif model.startswith("google/"):
            config_name = "gemini"

        llm = LLM(config_name=config_name)

        # Process request with LLM directly
        response = await llm.ask(
            messages=messages,
            temperature=temperature
        )

        # Format response
        result = {
            "id": f"chatcmpl-{str(uuid.uuid4())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_ssl_context():
    """Create SSL context for HTTPS"""
    cert_dir = os.path.join(os.path.dirname(__file__), "certs")
    os.makedirs(cert_dir, exist_ok=True)

    cert_file = os.path.join(cert_dir, "cert.pem")
    key_file = os.path.join(cert_dir, "key.pem")

    # Check if certificates exist, otherwise generate self-signed certificates
    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        print("Generating self-signed certificates...")
        os.system(
            f"openssl req -x509 -newkey rsa:4096 -nodes -out {cert_file} "
            f"-keyout {key_file} -days 365 -subj '/CN=localhost'"
        )

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    return context

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting Agent Orchestra API server at http://{host}:{port}")
    print(f"Agent endpoint: http://{host}:{port}/api/agent/run")
    print(f"Legacy chat endpoint: http://{host}:{port}/api/chat/completions")

    try:
        # Try to use HTTPS if certificates are available
        context = create_ssl_context()
        https_port = int(os.environ.get("HTTPS_PORT", 443))
        print(f"HTTPS also available on port {https_port}")

        # For port 80, we'll use the standard HTTP server instead of run_simple
        # since port 80 usually requires root privileges
        if port < 1024 and os.geteuid() != 0:
            print("Warning: Ports below 1024 typically require root privileges.")
            print("Consider using sudo or a reverse proxy like Nginx.")

        # Start the server
        app.run(host=host, port=port, ssl_context=context if port == 443 else None)
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Falling back to HTTP (not secure)...")
        app.run(host=host, port=port)
