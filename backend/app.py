from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from agent.graph import LangGraphAgent

app = FastAPI(title="LangGraph-style RAG Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = LangGraphAgent(knowledge_file=str(ROOT / "knowledge.txt"))
session_memory: dict[str, list[dict[str, str]]] = {}


class AskRequest(BaseModel):
    question: str
    session_id: str = "default"
    stream: bool = False
    latitude: float | None = None
    longitude: float | None = None


@app.get("/")
def home() -> dict:
    return {"message": "LangGraph-style AI agent API is running."}


@app.get("/history/{session_id}")
def get_history(session_id: str) -> dict:
    return {"session_id": session_id, "history": session_memory.get(session_id, [])}


@app.post("/ask")
def ask(request: AskRequest):
    history = session_memory.setdefault(request.session_id, [])
    answer = agent.ask(
        request.question,
        history=history,
        latitude=request.latitude,
        longitude=request.longitude,
    )
    history.append({"role": "user", "content": request.question})
    history.append({"role": "assistant", "content": answer})
    if len(history) > 12:
        history[:] = history[-12:]
    return PlainTextResponse(answer)
