from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Iterator

import requests

from vector_store import VectorStore


class SimpleRAGAgent:
    def __init__(self, knowledge_file: str | None = None):
        self.vector_store = VectorStore()
        self.memory: List[Dict[str, str]] = []
        project_root = Path(__file__).resolve().parent
        default_path = project_root / "knowledge.txt"
        self.knowledge_file = str(Path(knowledge_file).resolve()) if knowledge_file else str(default_path)
        self._load_knowledge()

    def _load_knowledge(self) -> None:
        with open(self.knowledge_file, "r", encoding="utf-8") as file:
            raw_text = file.read()

        chunks = [chunk.strip() for chunk in raw_text.split("\n\n") if chunk.strip()]
        self.vector_store.add_documents(chunks)

    def retrieve(self, question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.vector_store.search(question, top_k=top_k)

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "No previous conversation yet."

        parts = []
        for item in history[-8:]:
            role = item.get("role", "user").capitalize()
            content = item.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _trim_history(self, history: List[Dict[str, str]], max_turns: int = 2) -> List[Dict[str, str]]:
        if not history:
            return []
        trimmed = history[-max_turns * 2:]
        return trimmed

    def _is_arithmetic_question(self, question: str) -> bool:
        q = question.lower()
        arithmetic_tokens = [
            "+", "-", "*", "/", "plus", "minus", "multiply", "divide",
            "sum", "difference", "product", "quotient", "calculate", "math",
            "equation", "compute"
        ]
        if any(token in q for token in arithmetic_tokens):
            return True

        try:
            # Ignore simple expressions like "2+2" if they are purely numeric.
            import ast
            expr = q.replace("^", "**")
            ast.parse(expr, mode="eval")
            return bool(any(ch.isdigit() for ch in q) and any(ch in "+-*/" for ch in q))
        except Exception:
            return False

    def _filter_history_for_question(self, history: List[Dict[str, str]], question: str) -> List[Dict[str, str]]:
        if not history:
            return []
        if self._is_arithmetic_question(question):
            return []
        return self._trim_history(history, max_turns=2)

    def _tool_get_current_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _route_tool(self, question: str) -> tuple[str, Any]:
        q = question.lower()
        if any(keyword in q for keyword in ["time", "date", "today", "now"]):
            return "get_current_time", self._tool_get_current_time()
        return "search_knowledge", self.retrieve(question, top_k=3)

    def _query_ollama(self, prompt: str) -> str:
        payload = {
            "model": "llama3.2",
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

    def _stream_ollama(self, prompt: str) -> Iterator[str]:
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": True,
        }

        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60,
            stream=True,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue
            try:
                payload_data = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = payload_data.get("response", "")
            if text:
                yield text

    def _build_prompt(self, question: str, context: str, history: List[Dict[str, str]] | None = None) -> str:
        formatted_history = self._format_history(history or [])
        return f"""
You are a helpful assistant.
Instructions:
1. Use the retrieved context first to ground your answer.
2. If the context is missing or only partly relevant, use your best general knowledge and explain the gap clearly.
3. If the answer is not in the context, do not say "I don't know" just because the context is limited; instead, answer using your best reasoning and state that the context is limited.
4. Do not invent facts. Be honest about uncertainty, but keep helping the user.
5. Keep conversational history separate from retrieved knowledge. Only use the last 2 turns of conversation history if relevant to the current question.
6. For arithmetic or pure calculation questions, ignore old conversational context and answer directly.

Conversation history:
{formatted_history}

Retrieved context:
{context}

User question:
{question}

Answer:
""".strip()

    def ask(self, question: str, history: List[Dict[str, str]] | None = None) -> str:
        combined_history = (history or []) + self.memory
        filtered_history = self._filter_history_for_question(combined_history, question)
        tool_name, tool_result = self._route_tool(question)

        if tool_name == "get_current_time":
            answer = f"The current time is {tool_result}."
            self.memory.append({"role": "user", "content": question})
            self.memory.append({"role": "assistant", "content": answer})
            self.memory = self._trim_history(self.memory, max_turns=2)
            return answer

        documents = tool_result
        if not documents:
            return "I do not have knowledge for that query yet."

        context = "\n\n".join(doc["content"] for doc in documents)
        prompt = self._build_prompt(question, context, filtered_history)

        try:
            answer = self._query_ollama(prompt)
            self.memory.append({"role": "user", "content": question})
            self.memory.append({"role": "assistant", "content": answer})
            self.memory = self._trim_history(self.memory, max_turns=2)
            return answer
        except Exception:
            fallback = self._fallback_answer(question, documents)
            self.memory.append({"role": "user", "content": question})
            self.memory.append({"role": "assistant", "content": fallback})
            self.memory = self._trim_history(self.memory, max_turns=2)
            return fallback

    def ask_stream(self, question: str, history: List[Dict[str, str]] | None = None) -> Iterator[str]:
        combined_history = (history or []) + self.memory
        filtered_history = self._filter_history_for_question(combined_history, question)
        tool_name, tool_result = self._route_tool(question)

        if tool_name == "get_current_time":
            answer = f"The current time is {tool_result}."
            self.memory.append({"role": "user", "content": question})
            self.memory.append({"role": "assistant", "content": answer})
            self.memory = self._trim_history(self.memory, max_turns=2)
            yield answer
            return

        documents = tool_result
        if not documents:
            yield "I do not have knowledge for that query yet."
            return

        context = "\n\n".join(doc["content"] for doc in documents)
        prompt = self._build_prompt(question, context, filtered_history)

        try:
            chunks: List[str] = []
            for chunk in self._stream_ollama(prompt):
                chunks.append(chunk)
                yield chunk

            self.memory.append({"role": "user", "content": question})
            self.memory.append({"role": "assistant", "content": "".join(chunks)})
            self.memory = self._trim_history(self.memory, max_turns=2)
        except Exception:
            fallback = self._fallback_answer(question, documents)
            self.memory.append({"role": "user", "content": question})
            self.memory.append({"role": "assistant", "content": fallback})
            self.memory = self._trim_history(self.memory, max_turns=2)
            yield fallback

    def _fallback_answer(self, question: str, documents: List[Dict[str, Any]]) -> str:
        context_text = "\n\n".join(doc["content"] for doc in documents)
        return (
            "Ollama is unavailable, so I am using the retrieved context as a fallback. "
            "If the context is limited, I will answer with the best general knowledge I can provide and clearly note the gap.\n\n"
            + context_text
            + "\n\n"
            + f"Question: {question}"
        )
