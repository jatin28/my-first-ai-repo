from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from agent.graph import LangGraphAgent

app = FastAPI(title="LangGraph-style RAG Agent API")
agent = LangGraphAgent(knowledge_file=str(ROOT / "knowledge.txt"))


class AskRequest(BaseModel):
    question: str
    session_id: str = "default"
    stream: bool = False


@app.get("/")
def home() -> dict:
    return {"message": "LangGraph-style RAG agent API is running."}


@app.post("/ask")
def ask(request: AskRequest):
    answer = agent.ask(request.question)
    return {"answer": answer, "session_id": request.session_id}
