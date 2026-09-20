from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    question: str
    history: List[Dict[str, str]]
    route: str
    retrieved_docs: List[Dict[str, Any]]
    context: str
    answer: str
    error: str
    latitude: Optional[float]
    longitude: Optional[float]
