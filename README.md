English | [中文](README_zh.md) | [한국어](README_ko.md) | [日本語](README_ja.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# 👋 Agent Orchestra

Agent Orchestra is an open-source framework for creating powerful, general-purpose AI agents that can solve a wide variety of tasks through orchestration of different capabilities and models.

Our goal is to provide a flexible, extensible architecture that enables developers to build agents that can:

- Work with multiple LLM providers (OpenAI, Google, Anthropic, and more)
- Use tools and APIs to accomplish complex tasks
- Navigate and interact with web content
- Execute code and terminal commands
- Adapt to different environments and contexts

Whether you're building a personal assistant, a research tool, or a specialized automation agent, Agent Orchestra provides the foundation for creating intelligent, capable AI systems.

## Project Demo

<video src="https://private-user-images.githubusercontent.com/61239030/420168772-6dcfd0d2-9142-45d9-b74e-d10aa75073c6.mp4?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDEzMTgwNTksIm5iZiI6MTc0MTMxNzc1OSwicGF0aCI6Ii82MTIzOTAzMC80MjAxNjg3NzItNmRjZmQwZDItOTE0Mi00NWQ5LWI3NGUtZDEwYWE3NTA3M2M2Lm1wND9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTAzMDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwMzA3VDAzMjIzOVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTdiZjFkNjlmYWNjMmEzOTliM2Y3M2VlYjgyNDRlZDJmOWE3NWZhZjE1MzhiZWY4YmQ3NjdkNTYwYTU5ZDA2MzYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.UuHQCgWYkh0OQq9qsUWqGsUbhG3i9jcZDAMeHjLt5T4" data-canonical-src="https://private-user-images.githubusercontent.com/61239030/420168772-6dcfd0d2-9142-45d9-b74e-d10aa75073c6.mp4?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDEzMTgwNTksIm5iZiI6MTc0MTMxNzc1OSwicGF0aCI6Ii82MTIzOTAzMC80MjAxNjg3NzItNmRjZmQwZDItOTE0Mi00NWQ5LWI3NGUtZDEwYWE3NTA3M2M2Lm1wND9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTAzMDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwMzA3VDAzMjIzOVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTdiZjFkNjlmYWNjMmEzOTliM2Y3M2VlYjgyNDRlZDJmOWE3NWZhZjE1MzhiZWY4YmQ3NjdkNTYwYTU5ZDA2MzYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.UuHQCgWYkh0OQq9qsUWqGsUbhG3i9jcZDAMeHjLt5T4" controls="controls" muted="muted" class="d-block rounded-bottom-2 border-top width-fit" style="max-height:640px; min-height: 200px"></video>

## Features

- **Multi-Model Support**: Use GPT-4, Claude, Gemini, and more
- **Tool Integration**: Built-in support for various tools and APIs
- **Browser Automation**: Navigate and interact with web content
- **Planning Capabilities**: Generate and execute complex plans
- **Flexible Architecture**: Extend with custom tools and components
- **Memory Management**: Efficient handling of context and history

## Installation

We provide two installation methods. Method 2 (using uv) is recommended for faster installation and better dependency management.

### Method 1: Using conda

1. Create a new conda environment:

```bash
conda create -n agent_orchestra python=3.12
conda activate agent_orchestra
```

2. Clone the repository:

```bash
git clone https://github.com/timonharz/agent-orchestra.git
cd agent-orchestra
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Method 2: Using uv (Recommended)

1. Install uv (A fast Python package installer and resolver):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:

```bash
git clone https://github.com/timonharz/agent-orchestra.git
cd agent-orchestra
```

3. Create a new virtual environment and activate it:

```bash
uv venv --python 3.12
source .venv/bin/activate  # On Unix/macOS
# Or on Windows:
# .venv\Scripts\activate
```

4. Install dependencies:

```bash
uv pip install -r requirements.txt
```

### Browser Automation Tool (Optional)
```bash
playwright install
```

## Configuration

Agent Orchestra requires configuration for the LLM APIs it uses. Follow these steps to set up your configuration:

1. Create a `config.toml` file in the `config` directory (you can copy from the example):

```bash
cp config/config.example.toml config/config.toml
```

2. Edit `config/config.toml` to add your API keys and customize settings:

```toml
# Global LLM configuration
[llm]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "sk-..."  # Replace with your actual API key
max_tokens = 4096
temperature = 0.0

# Optional configuration for specific LLM models
[llm.vision]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "sk-..."  # Replace with your actual API key
```

### Using Google Gemini Models

To use Google Gemini models, copy the Gemini configuration example:

```bash
cp config/config.example-gemini.toml config/config.toml
```

Then edit `config/config.toml` to add your Google API key:

```toml
# Global LLM configuration for Google Gemini
[llm]
model = "gemini-2.0-flash-001"                                          # The LLM model to use
base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"   # API endpoint URL
api_key = "YOUR_API_KEY"                                                # Your API key
temperature = 0.0                                                       # Controls randomness
max_tokens = 8096                                                       # Maximum number of tokens in the response
```

## Quick Start

One line for running Agent Orchestra:

```bash
python main.py
```

Then input your idea via terminal!

For MCP tool version, you can run:
```bash
python run_mcp.py
```

For multi-agent version, you can run:

```bash
python run_flow.py
```

## How to Contribute

We welcome any contributions to help improve Agent Orchestra! Feel free to submit issues or pull requests for:

- Bug fixes and improvements
- New features and tools
- Documentation updates
- Performance optimizations

Before submitting a pull request, please use the pre-commit tool to check your changes. Run `pre-commit run --all-files` to execute the checks.

## License

Agent Orchestra is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project builds upon and draws inspiration from various open-source projects in the AI agent space. We extend our gratitude to all contributors of these projects for their valuable work.

Special thanks to [anthropic-computer-use](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo) and [browser-use](https://github.com/browser-use/browser-use) for providing foundational capabilities.

## Deployment Options

### Option 1: Direct Deployment (Not Recommended for Production)

Run the server directly, but note that port 80 requires root privileges:

```bash
sudo python3 server.py
```

Alternatively, use a higher port number:

```bash
PORT=8080 python3 server.py
```

### Option 2: Systemd Service

Use the provided deployment script:

```bash
sudo ./deploy.sh
```

This creates and starts a systemd service running on port 80.

### Option 3: Docker (Recommended)

The easiest way to run the server without root privileges:

```bash
docker-compose up -d
```

### Option 4: Nginx with HTTPS (Best for Production)

For a production environment, use Nginx as a reverse proxy with proper SSL certificates:

1. Run the deployment script with your domain name:

```bash
sudo ./deploy-with-nginx.sh your-domain.com
```

This script:
- Installs Nginx and Certbot
- Configures the Agent Orchestra app to run on port 8080
- Sets up Nginx as a reverse proxy
- Obtains and configures SSL certificates via Let's Encrypt
- Configures HTTP to HTTPS redirection

Your API will be accessible at `https://your-domain.com`.

#### Manual Setup

If you prefer to set up Nginx manually:

1. Run the server on a non-privileged port:
```bash
PORT=8080 python3 server.py
```

2. Install Nginx:
```bash
sudo apt-get install nginx
```

3. Use our provided Nginx config:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/agent-orchestra
```

4. Edit the config file to match your domain:
```bash
sudo nano /etc/nginx/sites-available/agent-orchestra
```

5. Enable the site and get SSL certificates:
```bash
sudo ln -s /etc/nginx/sites-available/agent-orchestra /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com
sudo systemctl restart nginx
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/models` - List available models
- `POST /api/agent/run` - Run agent with messages
- `POST /api/chat/completions` - Legacy chat completion API
