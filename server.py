import os
import ssl
import time
import uuid
from typing import Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.serving import run_simple

from app.llm import LLM
from app.schema import Message

app = Flask(__name__)
CORS(app)

# Initialize LLM client
llm_client = None

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "OpenManus API"})

@app.route("/api/models", methods=["GET"])
def list_models():
    """List available models"""
    models = {
        "models": [
            {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "OpenAI via OpenRouter"},
            {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic via OpenRouter"},
            {"id": "mistral/mistral-large", "name": "Mistral Large", "provider": "Mistral via OpenRouter"}
        ]
    }
    return jsonify(models)

@app.route("/api/chat/completions", methods=["POST"])
async def chat_completions():
    """Process chat completion requests"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        # Extract request parameters
        model = data.get("model", "openai/gpt-4o")
        messages = data.get("messages", [])
        stream = data.get("stream", False)
        temperature = data.get("temperature", 0.7)
        system_message = next((msg for msg in messages if msg.get("role") == "system"), None)

        # Format messages for LLM
        system_msgs = [system_message] if system_message else None
        user_msgs = [msg for msg in messages if msg.get("role") != "system"]

        # Get LLM instance based on model name
        config_name = "default"
        if model.startswith("anthropic/"):
            config_name = "anthropic"
        elif model.startswith("mistral/"):
            config_name = "mistral"

        global llm_client
        if not llm_client:
            llm_client = {}

        if config_name not in llm_client:
            llm_client[config_name] = LLM(config_name=config_name)

        # Process request with LLM
        response = await llm_client[config_name].ask(
            messages=user_msgs,
            system_msgs=system_msgs,
            stream=stream,
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
    port = int(os.environ.get("PORT", 8443))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting HTTPS API server at https://{host}:{port}")

    try:
        context = create_ssl_context()
        run_simple(host, port, app, ssl_context=context)
    except Exception as e:
        print(f"Failed to start server with HTTPS: {e}")
        print("Falling back to HTTP (not secure)...")
        app.run(host=host, port=port)
