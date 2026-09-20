import importlib.util
from pathlib import Path

from .graph import LangGraphAgent

__all__ = ["LangGraphAgent", "SimpleRAGAgent"]

_legacy_module_path = Path(__file__).resolve().parent.parent / "agent.py"
_spec = importlib.util.spec_from_file_location("legacy_agent_module", _legacy_module_path)
if _spec is not None and _spec.loader is not None:
    _legacy_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_legacy_module)
    SimpleRAGAgent = _legacy_module.SimpleRAGAgent
else:
    SimpleRAGAgent = None
