from __future__ import annotations

from typing import List, Dict, Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.documents: List[str] = []
        self.index: faiss.Index | None = None

    def add_documents(self, texts: List[str]) -> None:
        if not texts:
            return

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)

        self.index.add(embeddings)
        self.documents.extend(texts)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if self.index is None or not self.documents:
            return []

        query_vector = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        k = min(top_k, len(self.documents))
        scores, indices = self.index.search(query_vector, k)

        results: List[Dict[str, Any]] = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            results.append({
                "content": self.documents[int(index)],
                "score": float(score),
            })

        return results
