from __future__ import annotations

from typing import Dict, List


class MemoryManager:
    def __init__(self, max_turns: int = 2):
        self.max_turns = max_turns
        self.items: List[Dict[str, str]] = []

    def append(self, question: str, answer: str) -> None:
        self.items.append({"role": "user", "content": question})
        self.items.append({"role": "assistant", "content": answer})
        self.items = self.trim(self.items)

    def trim(self, history: List[Dict[str, str]] | None = None) -> List[Dict[str, str]]:
        history = history if history is not None else self.items
        if not history:
            return []
        return history[-self.max_turns * 2:]

    def filtered_for_question(self, question: str, history: List[Dict[str, str]] | None = None) -> List[Dict[str, str]]:
        history = history if history is not None else self.items
        if not history:
            return []

        q = question.lower()
        arithmetic_tokens = [
            "+", "-", "*", "/", "plus", "minus", "multiply", "divide",
            "sum", "difference", "product", "quotient", "calculate", "math",
            "equation", "compute",
        ]
        if any(token in q for token in arithmetic_tokens):
            return []

        return self.trim(history)

    def get(self) -> List[Dict[str, str]]:
        return self.items
