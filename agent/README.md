# Agent package

This project now uses a LangGraph-style architecture to separate responsibility across a small set of modules.

## Structure

- `agent/state.py`  
  Defines the shared state object for the graph.

- `agent/memory.py`  
  Keeps the last 2 conversation turns and strips irrelevant history for arithmetic or tool-based tasks.

- `agent/router.py`  
  Decides whether the request should go to tool execution, retrieval, or direct generation.

- `agent/retriever.py`  
  Wraps the vector search and turns the retrieved documents into a single context string.

- `agent/tools.py`  
  Implements lightweight built-in tools such as current time and arithmetic evaluation.

- `agent/generator.py`  
  Calls Ollama locally and builds the final prompt.

- `agent/graph.py`  
  Orchestrates the behavior as a graph with explicit conditional branches.

## Graph flow

The agent graph follows this flow:

1. `route_input`  
   Determines the route: `tool`, `retrieve_context`, or `generate_answer`.

2. `check_memory`  
   Cleans conversation history before context is assembled.

3. `retrieve_context`  
   Uses the vector store to fetch matching documents.

4. `run_tool`  
   Handles built-in operations such as time and arithmetic.

5. `generate_answer`  
   Builds a prompt and sends it to Ollama.

6. `finalize`  
   Ensures the answer is always returned.

## Why this layout matters

This separates concerns so the project is easier to extend:

- Routing is easy to change
- Retrieval is isolated from prompt building
- Tools remain independent from the model layer
- Memory can be tuned without changing the rest of the app

## Relationship to the previous version

The original prototype kept all logic in one file. This refactor turns it into a small multi-file agent architecture that is closer to real-world LangGraph or workflow-based agent implementations.

## Example usage

```python
from agent.graph import LangGraphAgent

agent = LangGraphAgent(knowledge_file="knowledge.txt")
answer = agent.ask("What is RAG?")
print(answer)
```
