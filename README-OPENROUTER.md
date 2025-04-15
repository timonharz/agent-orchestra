# OpenRouter Integration for OpenManus

This extension adds support for [OpenRouter](https://openrouter.ai) to OpenManus, allowing you to access a variety of AI models from different providers through a single API.

## Setup

1. **Get API Key**: Sign up at [OpenRouter](https://openrouter.ai) and get your API key.

2. **Configure OpenManus**: Copy the example configuration and update with your API key:

```bash
cp config/config.example-model-openrouter.toml config/config.toml
```

Then edit `config/config.toml` and replace `<OPENROUTER_API_KEY>` with your actual API key.

## Configuration Options

The `config.example-model-openrouter.toml` file provides a template with the following settings:

```toml
[llm]
model = "openai/gpt-4o"  # Format is "provider/model"
base_url = "https://openrouter.ai/api/v1"
api_key = "<OPENROUTER_API_KEY>"
api_type = "openrouter"
api_version = ""  # Leave empty for OpenRouter
max_tokens = 4096
temperature = 0.7
```

You can define multiple model configurations:

```toml
[llm.anthropic]
model = "anthropic/claude-3-opus"
api_type = "openrouter"
temperature = 0.5
```

## Available Models

OpenRouter provides access to various models from providers including:

- OpenAI: `openai/gpt-4o`, `openai/gpt-4-turbo`, etc.
- Anthropic: `anthropic/claude-3-opus`, `anthropic/claude-3-sonnet`, etc.
- Mistral: `mistral/mistral-large`, `mistral/mistral-small`, etc.
- Many more: See [OpenRouter models](https://openrouter.ai/docs#models)

## Using the API Server

The `server.py` script provides an HTTPS REST API server that exposes the OpenRouter models.

### Running with Docker (Recommended)

The easiest way to run the server is with Docker and Docker Compose:

1. Build and start the container:
```bash
docker-compose up -d
```

2. Check the logs:
```bash
docker-compose logs -f
```

3. Stop the server:
```bash
docker-compose down
```

### Running Directly

If you prefer to run without Docker:

```bash
python server.py
```

The server will start on port 8443 by default. It will automatically generate self-signed SSL certificates if needed.

### API Endpoints

#### Health Check
```
GET /health
```

#### List Models
```
GET /api/models
```

#### Chat Completions
```
POST /api/chat/completions
```

Request body:
```json
{
  "model": "openai/gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "stream": false
}
```

## Docker Setup Details

The application is containerized using Docker for easy deployment:

- **Dockerfile**: Defines the container with all necessary dependencies
- **docker-compose.yml**: Simplifies container management with volume mounts for config and certificates

### Customizing Docker Setup

You can customize the Docker setup by:

1. Modifying environment variables in `docker-compose.yml`
2. Changing the port mapping (default is 8443:8443)
3. Adding additional volume mounts if needed

For security in production:
```yaml
volumes:
  - ./certs:/app/certs  # Mount your real SSL certificates here
  - ./config:/app/config
```

## Example Code

### Python

```python
import requests
import json

url = "https://localhost:8443/api/chat/completions"
payload = {
    "model": "openai/gpt-4o",
    "messages": [{"role": "user", "content": "What's the tallest mountain?"}],
    "stream": False
}

# Disable SSL verification for self-signed certs in development
response = requests.post(url, json=payload, verify=False)
print(response.json())
```

### JavaScript

```javascript
async function getCompletion() {
  const response = await fetch('https://localhost:8443/api/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'anthropic/claude-3-opus',
      messages: [{ role: 'user', content: 'What's the tallest mountain?' }],
    }),
  });

  const data = await response.json();
  console.log(data.choices[0].message.content);
}
```

## Troubleshooting

- **SSL Certificate Issues**: For production, replace the self-signed certificates in the `certs` directory with proper SSL certificates.
- **API Key Authentication**: Make sure your OpenRouter API key is valid and has sufficient credits.
- **Model Availability**: If a model is unavailable, try another one from the same provider.
- **Docker Issues**:
  - Check container logs: `docker-compose logs -f`
  - Ensure ports are not in use: `lsof -i :8443`
  - Verify config volume is mounted correctly
