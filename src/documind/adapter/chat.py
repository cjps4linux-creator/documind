from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from documind.schemas import Provider


class LLMError(Exception):
    pass


class ChatAdapter(ABC):
    @abstractmethod
    async def chat(self, messages: Sequence[dict[str, str]]) -> str:
        raise NotImplementedError


class OpenAIChatAdapter(ChatAdapter):
    def __init__(self, api_key: str | None, model: str = "gpt-4o-mini") -> None:
        import openai

        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(self, messages: Sequence[dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(model=self.model, messages=list(messages))
        message = response.choices[0].message.content or ""
        return message


class BedrockChatAdapter(ChatAdapter):
    def __init__(self, region: str, model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0") -> None:
        self.region = region
        self.model_id = model_id

    async def chat(self, messages: Sequence[dict[str, str]]) -> str:
        import asyncio
        import json

        system = next((m["content"] for m in messages if m["role"] == "system"), "You are a helpful assistant.")
        user_messages = [m for m in messages if m["role"] != "system"]
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": system,
            "messages": user_messages,
        }

        loop = asyncio.get_running_loop()
        body_bytes = await loop.run_in_executor(None, json.dumps, payload)
        response = await loop.run_in_executor(None, self._invoke_model, body_bytes)
        body = json.loads(response["body"].read())
        content = body.get("content", [])
        if not content:
            raise LLMError("Empty response from Bedrock.")
        return content[0].get("text", "")

    def _invoke_model(self, body: str):
        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.region)
        return client.invoke_model(modelId=self.model_id, body=body)


def build_chat_adapter(provider: Provider, **kwargs) -> ChatAdapter:
    if provider == Provider.bedrock:
        return BedrockChatAdapter(region=kwargs.get("aws_region", "us-east-1"), model_id=kwargs.get("bedrock_chat_model_id"))
    return OpenAIChatAdapter(api_key=kwargs.get("openai_api_key"), model=kwargs.get("openai_chat_model", "gpt-4o-mini"))
