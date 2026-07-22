from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from documind.schemas import Provider


class EmbeddingError(Exception):
    pass


class EmbeddingAdapter(ABC):
    @abstractmethod
    async def embed(self, texts: Iterable[str]) -> list[list[float]]:
        raise NotImplementedError

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed([text]))[0]


class OpenAIEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimensions: int = 1536) -> None:
        import openai

        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    async def embed(self, texts: Iterable[str]) -> list[list[float]]:
        import openai

        input_texts = [text.replace("\n", " ") for text in texts]
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=input_texts,
                dimensions=self.dimensions,
            )
        except openai.OpenAIError as exc:
            raise EmbeddingError(f"OpenAI embedding failed: {exc}") from exc
        return [item.embedding for item in response.data]


class BedrockEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, region: str, model_id: str = "amazon.titan-embed-text-v2:0", dimensions: int = 1024) -> None:
        self.region = region
        self.model_id = model_id
        self.dimensions = dimensions

    async def embed(self, texts: Iterable[str]) -> list[list[float]]:
        import asyncio
        import json

        loop = asyncio.get_running_loop()
        responses: list[list[float]] = []
        for text in texts:
            body = json.dumps(
                {
                    "inputText": text,
                    "dimensions": self.dimensions,
                    "normalize": True,
                }
            )
            response = await loop.run_in_executor(None, self._invoke_model, body)
            responses.append(response)
        return responses

    def _invoke_model(self, body: str) -> list[float]:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.region)
        response = client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(response["body"].read())
        embedding = payload.get("embedding") or []
        if not embedding:
            raise EmbeddingError("Empty embedding from Bedrock.")
        return embedding


def build_embedding_adapter(provider: Provider, **kwargs) -> EmbeddingAdapter:
    if provider == Provider.bedrock:
        region = kwargs.get("region", "us-east-1")
        model_id = kwargs.get("bedrock_embedding_model_id", "amazon.titan-embed-text-v2:0")
        return BedrockEmbeddingAdapter(region=region, model_id=model_id)
    api_key = kwargs.get("api_key", "")
    model = kwargs.get("openai_embedding_model", "text-embedding-3-small")
    return OpenAIEmbeddingAdapter(api_key=api_key, model=model)
