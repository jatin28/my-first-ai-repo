from __future__ import annotations

from typing import Dict, List

import requests


class Generator:
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name

    def build_prompt(self, question: str, context: str, history: List[Dict[str, str]]) -> str:
        formatted_history = self._format_history(history)
        return f"""
You are a helpful assistant.
Use the retrieved context first.
Then apply your own reasoning.
If the context is missing or only partly relevant, answer using your best general knowledge and clearly say the context is limited.
Do not invent facts.

Conversation history:
{formatted_history}

Retrieved context:
{context}

User question:
{question}

Answer:
""".strip()

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "No previous conversation yet."
        parts = []
        for item in history[-8:]:
            role = item.get("role", "user").capitalize()
            content = item.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def generate(self, question: str, context: str, history: List[Dict[str, str]]) -> str:
        prompt = self.build_prompt(question, context, history)
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
