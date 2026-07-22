from __future__ import annotations

from pathlib import Path

import pytest
from respx import MockRouter

from documind.adapter.chat import OpenAIChatAdapter
from documind.embeddings.adapter import OpenAIEmbeddingAdapter
from documind.schemas import AskRequest, Provider
from documind.services.retrieval import RetrievalService


def test_embedding_adapter_http_error():
    adapter = OpenAIEmbeddingAdapter(api_key="test")
    with pytest.raises(Exception):
        import asyncio
        asyncio.run(adapter.embed(["abc"]))


def test_chat_adapter_builds_openai():
    adapter = OpenAIChatAdapter(api_key="test", model="gpt-4o-mini")
    assert adapter.model == "gpt-4o-mini"
