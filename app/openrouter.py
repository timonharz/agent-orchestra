import json
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, AsyncIterator

import aiohttp
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk

# Class to handle OpenAI-style response formatting
class OpenAIResponse:
    def __init__(self, data):
        # Recursively convert nested dicts and lists to OpenAIResponse objects
        for key, value in data.items():
            if isinstance(value, dict):
                value = OpenAIResponse(value)
            elif isinstance(value, list):
                value = [
                    OpenAIResponse(item) if isinstance(item, dict) else item
                    for item in value
                ]
            setattr(self, key, value)

    def model_dump(self, *args, **kwargs):
        # Convert object to dict and add timestamp
        data = self.__dict__
        data["created_at"] = datetime.now().isoformat()
        return data


class OpenRouterClient:
    def __init__(self):
        # Initialize OpenRouter client
        try:
            self.api_key = None  # Will be set from LLMSettings
            self.base_url = "https://openrouter.ai/api/v1"
            self.chat = Chat(self)
        except Exception as e:
            print(f"Error initializing OpenRouter client: {e}")
            sys.exit(1)

    def set_api_key(self, api_key):
        self.api_key = api_key


class Chat:
    def __init__(self, client):
        self.completions = ChatCompletions(client)


class ChatCompletions:
    def __init__(self, client):
        self.client = client

    def _create_headers(self):
        return {
            "Authorization": f"Bearer {self.client.api_key}",
            "Content-Type": "application/json"
        }

    def _create_payload(self, model, messages, max_tokens, temperature, stream, **kwargs):
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }

        # Add optional parameters
        if kwargs.get("tools"):
            payload["tools"] = kwargs.get("tools")

        if kwargs.get("tool_choice"):
            payload["tool_choice"] = kwargs.get("tool_choice")

        return payload

    def _parse_sse_chunk(self, chunk):
        """Parse an SSE chunk received from OpenRouter"""
        if not chunk.strip():
            return None

        if chunk.startswith('data: '):
            data = chunk[6:].strip()
            if data == '[DONE]':
                return None

            try:
                data_obj = json.loads(data)
                # Create OpenAI-compatible response
                return data_obj
            except json.JSONDecodeError:
                return None
        return None

    async def create(self, **kwargs) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        model = kwargs.get("model")
        messages = kwargs.get("messages")
        max_tokens = kwargs.get("max_tokens", 1024)
        temperature = kwargs.get("temperature", 0.7)
        stream = kwargs.get("stream", False)

        if stream:
            return self._create_streaming_response(model, messages, max_tokens, temperature, **kwargs)
        else:
            return await self._create_non_streaming_response(model, messages, max_tokens, temperature, **kwargs)

    async def _create_non_streaming_response(self, model, messages, max_tokens, temperature, **kwargs):
        """Send a non-streaming request to OpenRouter"""
        url = f"{self.client.base_url}/chat/completions"
        headers = self._create_headers()
        payload = self._create_payload(model, messages, max_tokens, temperature, False, **kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {response.status} - {error_text}")

                data = await response.json()
                return OpenAIResponse(data)

    async def _create_streaming_response(self, model, messages, max_tokens, temperature, **kwargs):
        """Generator function for streaming responses from OpenRouter"""
        url = f"{self.client.base_url}/chat/completions"
        headers = self._create_headers()
        payload = self._create_payload(model, messages, max_tokens, temperature, True, **kwargs)

        buffer = ""
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {response.status} - {error_text}")

                async for chunk_bytes in response.content.iter_any():
                    chunk_text = chunk_bytes.decode('utf-8')
                    buffer += chunk_text

                    while True:
                        line_end = buffer.find('\n')
                        if line_end == -1:
                            break

                        line = buffer[:line_end].strip()
                        buffer = buffer[line_end + 1:]

                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break

                            try:
                                data_obj = json.loads(data)
                                # Create OpenAI-compatible chunk response
                                chunk_data = {
                                    "id": data_obj.get("id", f"chatcmpl-{uuid.uuid4()}"),
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": model,
                                    "choices": data_obj.get("choices", [])
                                }
                                yield OpenAIResponse(chunk_data)
                            except json.JSONDecodeError:
                                pass
