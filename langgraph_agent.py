from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, TypedDict

import requests
from langgraph.graph import END, StateGraph

from vector_store import VectorStore


class AgentState(TypedDict):
    question: str
    history: List[Dict[str, str]]
    route: str
    retrieved_docs: List[Dict[str, Any]]
    context: str
    answer: str
    error: str


class LangGraphAgent:
    """A LangGraph-style refactor of the current custom RAG agent."""

    def __init__(self, knowledge_file: str | None = None):
        self.vector_store = VectorStore()
        self.memory: List[Dict[str, str]] = []
        project_root = Path(__file__).resolve().parent
        default_path = project_root / "knowledge.txt"
        self.knowledge_file = str(Path(knowledge_file).resolve()) if knowledge_file else str(default_path)
        self._load_knowledge()
        self.graph = self.build_graph()

    def _load_knowledge(self) -> None:
        with open(self.knowledge_file, "r", encoding="utf-8") as file:
            raw_text = file.read()

        chunks = [chunk.strip() for chunk in raw_text.split("\n\n") if chunk.strip()]
        self.vector_store.add_documents(chunks)

    def _trim_history(self, history: List[Dict[str, str]], max_turns: int = 2) -> List[Dict[str, str]]:
        if not history:
            return []
        return history[-max_turns * 2:]

    def _is_arithmetic_question(self, question: str) -> bool:
        q = question.lower()
        arithmetic_tokens = [
            "+", "-", "*", "/", "plus", "minus", "multiply", "divide",
            "sum", "difference", "product", "quotient", "calculate", "math",
            "equation", "compute",
        ]
        if any(token in q for token in arithmetic_tokens):
            return True

        try:
            import ast
            expr = q.replace("^", "**")
            ast.parse(expr, mode="eval")
            return bool(any(ch.isdigit() for ch in q) and any(ch in "+-*/" for ch in q))
        except Exception:
            return False

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "No previous conversation yet."

        parts = []
        for item in history[-8:]:
            role = item.get("role", "user").capitalize()
            content = item.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _route_question(self, question: str) -> str:
        q = question.lower()
        if any(keyword in q for keyword in ["time", "date", "today", "now"]):
            return "tool"
        if self._is_arithmetic_question(question):
            return "direct"
        return "retrieve"

    def route_input(self, state: AgentState) -> AgentState:
        question = state["question"]
        state["route"] = self._route_question(question)
        return state

    def route_decision(self, state: AgentState) -> Literal["retrieve_context", "run_tool", "generate_answer"]:
        route = state.get("route", "retrieve")
        if route == "tool":
            return "run_tool"
        if route == "direct":
            return "generate_answer"
        return "retrieve_context"

    def retrieve_context(self, state: AgentState) -> AgentState:
        question = state["question"]
        docs = self.vector_store.search(question, top_k=3)
        state["retrieved_docs"] = docs
        state["context"] = "\n\n".join(doc["content"] for doc in docs)
        return state

    def run_tool(self, state: AgentState) -> AgentState:
        question = state["question"]
        q = question.lower()
        if any(keyword in q for keyword in ["time", "date", "today", "now"]):
            state["answer"] = f"The current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            return state

        if self._is_arithmetic_question(question):
            try:
                expr = question.replace("x", "*")
                expr = expr.replace("÷", "/")
                expr = expr.replace("^", "**")
                result = eval(expr, {"__builtins__": {}}, {})
                state["answer"] = str(result)
                return state
            except Exception:
                state["answer"] = "I can do the arithmetic, but the expression is not valid."
                return state

        state["answer"] = "Tool routing did not find a supported action."
        return state

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

    def build_prompt(self, question: str, context: str, history: List[Dict[str, str]]) -> str:
        formatted_history = self._format_history(history)
        return f"""
You are a helpful assistant.
Use the retrieved context first.
Then apply your own reasoning.
If the context is missing or only partly relevant, say so and answer using your best general knowledge.
Do not invent facts.

Conversation history:
{formatted_history}

Retrieved context:
{context}

User question:
{question}

Answer:
""".strip()

    def generate_answer(self, state: AgentState) -> AgentState:
        question = state["question"]
        history = self._trim_history(state.get("history", []), max_turns=2)
        context = state.get("context", "")

        if not context:
            context = "No retrieved context is available for this question."

        prompt = self.build_prompt(question, context, history)
        try:
            state["answer"] = self._query_ollama(prompt)
        except Exception as exc:
            state["error"] = str(exc)
            state["answer"] = (
                "Ollama is unavailable, so I can only respond with the retrieved context and my best reasoning.\n\n"
                f"Context: {context}"
            )
        return state

    def finalize_response(self, state: AgentState) -> AgentState:
        final_answer = state.get("answer", "")
        if not final_answer:
            state["answer"] = "I could not produce an answer."
        return state

    def build_graph(self):
        builder = StateGraph(AgentState)

        builder.add_node("route_input", self.route_input)
        builder.add_node("retrieve_context", self.retrieve_context)
        builder.add_node("run_tool", self.run_tool)
        builder.add_node("generate_answer", self.generate_answer)
        builder.add_node("finalize", self.finalize_response)

        builder.set_entry_point("route_input")
        builder.add_conditional_edges(
            "route_input",
            self.route_decision,
            {
                "retrieve_context": "retrieve_context",
                "run_tool": "run_tool",
                "generate_answer": "generate_answer",
            },
        )
        builder.add_edge("retrieve_context", "generate_answer")
        builder.add_edge("run_tool", "finalize")
        builder.add_edge("generate_answer", "finalize")
        builder.add_edge("finalize", END)

        return builder.compile()

    def ask(self, question: str, history: List[Dict[str, str]] | None = None) -> str:
        prior_history = self._trim_history((history or []) + self.memory, max_turns=2)
        initial_state: AgentState = {
            "question": question,
            "history": prior_history,
            "route": "",
            "retrieved_docs": [],
            "context": "",
            "answer": "",
            "error": "",
        }

        result = self.graph.invoke(initial_state)
        answer = result.get("answer", "")
        self.memory.append({"role": "user", "content": question})
        self.memory.append({"role": "assistant", "content": answer})
        self.memory = self._trim_history(self.memory, max_turns=2)
        return answer


if __name__ == "__main__":
    agent = LangGraphAgent()
    print(agent.ask("What is RAG?"))
    print(agent.ask("What is 2 + 2?"))
