from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from agent.generator import Generator
from agent.memory import MemoryManager
from agent.retriever import Retriever
from agent.router import route_question
from agent.state import AgentState
from agent.tools import evaluate_expression, get_current_time, get_weather_for_location
from vector_store import VectorStore


class LangGraphAgent:
    def __init__(self, knowledge_file: str | None = None):
        self.vector_store = VectorStore()
        self.memory = MemoryManager(max_turns=2)
        self.retriever = Retriever(self.vector_store)
        self.generator = Generator(model_name="llama3.2")
        self.load_knowledge(knowledge_file)
        self.graph = self._build_graph()

    def load_knowledge(self, knowledge_file: str | None = None) -> None:
        if knowledge_file is None:
            knowledge_file = "knowledge.txt"

        with open(knowledge_file, "r", encoding="utf-8") as handle:
            content = handle.read()

        chunks = [part.strip() for part in content.split("\n\n") if part.strip()]
        self.vector_store.add_documents(chunks)

    def route_input(self, state: AgentState) -> AgentState:
        state["route"] = route_question(state["question"])
        return state

    def check_memory(self, state: AgentState) -> AgentState:
        history = state.get("history", [])
        if not history:
            state["history"] = []
            return state

        q = state["question"].lower()
        if any(keyword in q for keyword in ["time", "date", "today", "now"]) or "+" in state["question"] or "-" in state["question"] or "*" in state["question"] or "/" in state["question"]:
            state["history"] = []
        else:
            state["history"] = self.memory.trim(history)
        return state

    def retrieve_context(self, state: AgentState) -> AgentState:
        docs = self.retriever.retrieve(state["question"], top_k=3)
        state["retrieved_docs"] = docs
        state["context"] = self.retriever.build_context(docs)
        return state

    def run_tool(self, state: AgentState) -> AgentState:
        q = state["question"].lower()
        if any(keyword in q for keyword in ["time", "date", "today", "now"]):
            state["answer"] = f"The current time is {get_current_time()}."
            return state

        if "+" in state["question"] or "-" in state["question"] or "*" in state["question"] or "/" in state["question"]:
            state["answer"] = evaluate_expression(state["question"])
            return state

        state["answer"] = "No supported tool matched this request."
        return state

    def run_weather(self, state: AgentState) -> AgentState:
        state["answer"] = get_weather_for_location(
            state["question"],
            state.get("latitude"),
            state.get("longitude"),
        )
        return state

    def generate_answer(self, state: AgentState) -> AgentState:
        history = self.memory.filtered_for_question(state["question"], state.get("history", []))
        context = state.get("context", "") or "No retrieved context is available for this question."
        state["answer"] = self.generator.generate(state["question"], context, history)
        return state

    def finalize(self, state: AgentState) -> AgentState:
        if not state.get("answer"):
            state["answer"] = "I could not produce an answer."
        return state

    def decide_next(self, state: AgentState) -> Literal["memory", "tool", "weather", "retrieve_context", "generate_answer"]:
        route = state.get("route", "retrieve")
        if route == "tool":
            return "tool"
        if route == "weather":
            return "weather"
        if route == "direct":
            return "generate_answer"
        if state.get("history"):
            return "memory"
        return "retrieve_context"

    def _build_graph(self):
        builder = StateGraph(AgentState)

        builder.add_node("route_input", self.route_input)
        builder.add_node("check_memory", self.check_memory)
        builder.add_node("retrieve_context", self.retrieve_context)
        builder.add_node("run_tool", self.run_tool)
        builder.add_node("run_weather", self.run_weather)
        builder.add_node("generate_answer", self.generate_answer)
        builder.add_node("finalize", self.finalize)

        builder.set_entry_point("route_input")
        builder.add_conditional_edges(
            "route_input",
            self.decide_next,
            {
                "memory": "check_memory",
                "tool": "run_tool",
                "weather": "run_weather",
                "retrieve_context": "retrieve_context",
                "generate_answer": "generate_answer",
            },
        )
        builder.add_edge("check_memory", "retrieve_context")
        builder.add_edge("retrieve_context", "generate_answer")
        builder.add_edge("run_tool", "finalize")
        builder.add_edge("run_weather", "finalize")
        builder.add_edge("generate_answer", "finalize")
        builder.add_edge("finalize", END)

        return builder.compile()

    def ask(self, question: str, history: list[dict[str, str]] | None = None, latitude: float | None = None, longitude: float | None = None) -> str:
        if history is None:
            history = []

        merged_history = self.memory.trim((history or []) + self.memory.get())
        initial_state: AgentState = {
            "question": question,
            "history": merged_history,
            "route": "",
            "retrieved_docs": [],
            "context": "",
            "answer": "",
            "error": "",
            "latitude": latitude,
            "longitude": longitude,
        }

        result = self.graph.invoke(initial_state)
        answer = result.get("answer", "")
        self.memory.append(question, answer)
        return answer


if __name__ == "__main__":
    agent = LangGraphAgent(knowledge_file="knowledge.txt")
    print(agent.ask("What is RAG?"))
    print(agent.ask("What is 2 + 2?"))
