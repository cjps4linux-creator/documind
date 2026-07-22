from __future__ import annotations

import pytest
from documind.adapter.chat import OpenAIChatAdapter
from documind.embeddings.adapter import OpenAIEmbeddingAdapter


def test_embedding_adapter_http_error() -> None:
    adapter = OpenAIEmbeddingAdapter(api_key="test")
    with pytest.raises(Exception):
        import asyncio

        asyncio.run(adapter.embed(["abc"]))


def test_chat_adapter_builds_openai() -> None:
    adapter = OpenAIChatAdapter(api_key="test", model="gpt-4o-mini")
    assert adapter.model == "gpt-4o-mini"
