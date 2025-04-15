import json
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional, Union, AsyncIterator

import boto3
import aiohttp
from openai.types.chat import ChatCompletionChunk


# Global variables to track the current tool use ID across function calls
# Tmp solution
CURRENT_TOOLUSE_ID = None


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


# Main client class for interacting with Amazon Bedrock
class BedrockClient:
    def __init__(self):
        # Initialize Bedrock client, you need to configure AWS env first
        try:
            self.client = boto3.client("bedrock-runtime")
            self.chat = Chat(self.client)
        except Exception as e:
            print(f"Error initializing Bedrock client: {e}")
            sys.exit(1)


# Main client class for interacting with OpenRouter
class OpenRouterClient:
    def __init__(self):
        # Initialize OpenRouter client
        try:
            self.api_key = None  # Will be set from LLMSettings
            self.base_url = "https://openrouter.ai/api/v1"
            self.chat = OpenRouterChat(self)
        except Exception as e:
            print(f"Error initializing OpenRouter client: {e}")
            sys.exit(1)

    def set_api_key(self, api_key):
        self.api_key = api_key


# Chat interface class for Bedrock
class Chat:
    def __init__(self, client):
        self.completions = ChatCompletions(client)


# Chat interface class for OpenRouter
class OpenRouterChat:
    def __init__(self, client):
        self.completions = OpenRouterChatCompletions(client)


# Core class handling OpenRouter chat completions functionality
class OpenRouterChatCompletions:
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

    async def create(self, **kwargs) -> Union[OpenAIResponse, AsyncIterator[OpenAIResponse]]:
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


# Core class handling chat completions functionality for Bedrock
class ChatCompletions:
    def __init__(self, client):
        self.client = client

    def _convert_openai_tools_to_bedrock_format(self, tools):
        # Convert OpenAI function calling format to Bedrock tool format
        bedrock_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                bedrock_tool = {
                    "toolSpec": {
                        "name": function.get("name", ""),
                        "description": function.get("description", ""),
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": function.get("parameters", {}).get(
                                    "properties", {}
                                ),
                                "required": function.get("parameters", {}).get(
                                    "required", []
                                ),
                            }
                        },
                    }
                }
                bedrock_tools.append(bedrock_tool)
        return bedrock_tools

    def _convert_openai_messages_to_bedrock_format(self, messages):
        # Convert OpenAI message format to Bedrock message format
        bedrock_messages = []
        system_prompt = []
        for message in messages:
            if message.get("role") == "system":
                system_prompt = [{"text": message.get("content")}]
            elif message.get("role") == "user":
                bedrock_message = {
                    "role": message.get("role", "user"),
                    "content": [{"text": message.get("content")}],
                }
                bedrock_messages.append(bedrock_message)
            elif message.get("role") == "assistant":
                bedrock_message = {
                    "role": "assistant",
                    "content": [{"text": message.get("content")}],
                }
                openai_tool_calls = message.get("tool_calls", [])
                if openai_tool_calls:
                    bedrock_tool_use = {
                        "toolUseId": openai_tool_calls[0]["id"],
                        "name": openai_tool_calls[0]["function"]["name"],
                        "input": json.loads(
                            openai_tool_calls[0]["function"]["arguments"]
                        ),
                    }
                    bedrock_message["content"].append({"toolUse": bedrock_tool_use})
                    global CURRENT_TOOLUSE_ID
                    CURRENT_TOOLUSE_ID = openai_tool_calls[0]["id"]
                bedrock_messages.append(bedrock_message)
            elif message.get("role") == "tool":
                bedrock_message = {
                    "role": "user",
                    "content": [
                        {
                            "toolResult": {
                                "toolUseId": CURRENT_TOOLUSE_ID,
                                "content": [{"text": message.get("content")}],
                            }
                        }
                    ],
                }
                bedrock_messages.append(bedrock_message)
            else:
                raise ValueError(f"Invalid role: {message.get('role')}")
        return system_prompt, bedrock_messages

    def _convert_bedrock_response_to_openai_format(self, bedrock_response):
        # Convert Bedrock response format to OpenAI format
        content = ""
        if bedrock_response.get("output", {}).get("message", {}).get("content"):
            content_array = bedrock_response["output"]["message"]["content"]
            content = "".join(item.get("text", "") for item in content_array)
        if content == "":
            content = "."

        # Handle tool calls in response
        openai_tool_calls = []
        if bedrock_response.get("output", {}).get("message", {}).get("content"):
            for content_item in bedrock_response["output"]["message"]["content"]:
                if content_item.get("toolUse"):
                    bedrock_tool_use = content_item["toolUse"]
                    global CURRENT_TOOLUSE_ID
                    CURRENT_TOOLUSE_ID = bedrock_tool_use["toolUseId"]
                    openai_tool_call = {
                        "id": CURRENT_TOOLUSE_ID,
                        "type": "function",
                        "function": {
                            "name": bedrock_tool_use["name"],
                            "arguments": json.dumps(bedrock_tool_use["input"]),
                        },
                    }
                    openai_tool_calls.append(openai_tool_call)

        # Construct final OpenAI format response
        openai_format = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "created": int(time.time()),
            "object": "chat.completion",
            "system_fingerprint": None,
            "choices": [
                {
                    "finish_reason": bedrock_response.get("stopReason", "end_turn"),
                    "index": 0,
                    "message": {
                        "content": content,
                        "role": bedrock_response.get("output", {})
                        .get("message", {})
                        .get("role", "assistant"),
                        "tool_calls": openai_tool_calls
                        if openai_tool_calls != []
                        else None,
                        "function_call": None,
                    },
                }
            ],
            "usage": {
                "completion_tokens": bedrock_response.get("usage", {}).get(
                    "outputTokens", 0
                ),
                "prompt_tokens": bedrock_response.get("usage", {}).get(
                    "inputTokens", 0
                ),
                "total_tokens": bedrock_response.get("usage", {}).get("totalTokens", 0),
            },
        }
        return OpenAIResponse(openai_format)

    async def _invoke_bedrock(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[dict]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        **kwargs,
    ) -> OpenAIResponse:
        # Non-streaming invocation of Bedrock model
        (
            system_prompt,
            bedrock_messages,
        ) = self._convert_openai_messages_to_bedrock_format(messages)
        response = self.client.converse(
            modelId=model,
            system=system_prompt,
            messages=bedrock_messages,
            inferenceConfig={"temperature": temperature, "maxTokens": max_tokens},
            toolConfig={"tools": tools} if tools else None,
        )
        openai_response = self._convert_bedrock_response_to_openai_format(response)
        return openai_response

    async def _invoke_bedrock_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[dict]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        **kwargs,
    ) -> OpenAIResponse:
        # Streaming invocation of Bedrock model
        (
            system_prompt,
            bedrock_messages,
        ) = self._convert_openai_messages_to_bedrock_format(messages)
        response = self.client.converse_stream(
            modelId=model,
            system=system_prompt,
            messages=bedrock_messages,
            inferenceConfig={"temperature": temperature, "maxTokens": max_tokens},
            toolConfig={"tools": tools} if tools else None,
        )

        # Initialize response structure
        bedrock_response = {
            "output": {"message": {"role": "", "content": []}},
            "stopReason": "",
            "usage": {},
            "metrics": {},
        }
        bedrock_response_text = ""
        bedrock_response_tool_input = ""

        # Process streaming response
        stream = response.get("stream")
        if stream:
            for event in stream:
                if event.get("messageStart", {}).get("role"):
                    bedrock_response["output"]["message"]["role"] = event[
                        "messageStart"
                    ]["role"]
                if event.get("contentBlockDelta", {}).get("delta", {}).get("text"):
                    bedrock_response_text += event["contentBlockDelta"]["delta"]["text"]
                    print(
                        event["contentBlockDelta"]["delta"]["text"], end="", flush=True
                    )
                if event.get("contentBlockStop", {}).get("contentBlockIndex") == 0:
                    bedrock_response["output"]["message"]["content"].append(
                        {"text": bedrock_response_text}
                    )
                if event.get("contentBlockStart", {}).get("start", {}).get("toolUse"):
                    bedrock_tool_use = event["contentBlockStart"]["start"]["toolUse"]
                    tool_use = {
                        "toolUseId": bedrock_tool_use["toolUseId"],
                        "name": bedrock_tool_use["name"],
                    }
                    bedrock_response["output"]["message"]["content"].append(
                        {"toolUse": tool_use}
                    )
                    global CURRENT_TOOLUSE_ID
                    CURRENT_TOOLUSE_ID = bedrock_tool_use["toolUseId"]
                if event.get("contentBlockDelta", {}).get("delta", {}).get("toolUse"):
                    bedrock_response_tool_input += event["contentBlockDelta"]["delta"][
                        "toolUse"
                    ]["input"]
                    print(
                        event["contentBlockDelta"]["delta"]["toolUse"]["input"],
                        end="",
                        flush=True,
                    )
                if event.get("contentBlockStop", {}).get("contentBlockIndex") == 1:
                    bedrock_response["output"]["message"]["content"][1]["toolUse"][
                        "input"
                    ] = json.loads(bedrock_response_tool_input)
        print()
        openai_response = self._convert_bedrock_response_to_openai_format(
            bedrock_response
        )
        return openai_response

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        stream: Optional[bool] = True,
        tools: Optional[List[dict]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        **kwargs,
    ) -> OpenAIResponse:
        # Main entry point for chat completion
        bedrock_tools = []
        if tools is not None:
            bedrock_tools = self._convert_openai_tools_to_bedrock_format(tools)
        if stream:
            return self._invoke_bedrock_stream(
                model,
                messages,
                max_tokens,
                temperature,
                bedrock_tools,
                tool_choice,
                **kwargs,
            )
        else:
            return self._invoke_bedrock(
                model,
                messages,
                max_tokens,
                temperature,
                bedrock_tools,
                tool_choice,
                **kwargs,
            )
