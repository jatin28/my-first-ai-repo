from __future__ import annotations

from typing import Any, Dict, List

from vector_store import VectorStore


class Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(self, question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.vector_store.search(question, top_k=top_k)

    def build_context(self, docs: List[Dict[str, Any]]) -> str:
        return "\n\n".join(doc["content"] for doc in docs)
