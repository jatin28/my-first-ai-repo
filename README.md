# Minimal AI Agent with RAG and Vector Search

This project is a simple educational example of how an AI agent is built in practice.

It includes:
- a small "agent" loop
- a retrieval step (RAG)
- a vector database using FAISS
- an optional local LLM call through Ollama

## What this project demonstrates

You will see the following pattern:

1. User asks a question.
2. The agent searches a knowledge base using vector similarity.
3. Relevant chunks are retrieved.
4. Those chunks are passed to the LLM as context.
5. The LLM answers using that retrieved context.

This is the core idea behind RAG (Retrieval-Augmented Generation).

---

## Project structure

- `main.py` - entry point for the example
- `agent.py` - agent logic
- `vector_store.py` - vector database wrapper
- `knowledge.txt` - sample knowledge base
- `requirements.txt` - Python dependencies

---

## Installation

### 1) Create a virtual environment

```bash
cd my-first-ai-agent
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the app

```bash
python main.py
```

Example questions:
- What is an AI agent?
- What is RAG?
- How does a vector database work?
- What is the difference between a prompt and retrieval?

---

## Optional: run with Ollama locally

This project can call a local Ollama model if you have it installed.

### 1) Install Ollama

Follow instructions from the official Ollama website.

### 2) Pull a model

```bash
ollama pull llama3.2
```

### 3) Start the local server

```bash
ollama serve
```

### 4) Run the app again

```bash
python main.py
```

If Ollama is not running, the app will still work in a fallback mode and answer from retrieved context without the model.

---

## How the agent works

### 1) Knowledge base
The file `knowledge.txt` contains a few documents about AI concepts.

### 2) Embeddings
Each text chunk is converted into a numeric vector with a sentence embedding model such as `all-MiniLM-L6-v2`.

### 3) Vector DB
Those vectors are stored in FAISS, which enables fast nearest-neighbor search.

### 4) Retrieval
When a user asks a question, the app embeds the question and retrieves the most relevant chunks from the vector database.

### 5) Prompt construction
The app sends the retrieved chunks as context to the LLM.

### 6) Answer generation
The LLM answers using the provided context instead of relying only on its general training data.

---

## Why this is useful

This gives you a simple mental model for real AI agents:

- Agents take input
- They reason over tools or memory
- They do retrieval or workflows
- They use an LLM for final generation
- They can be connected to APIs, databases, or local services

---

## Real-world extension ideas

You can extend this into a more realistic agent by adding:
- a tool call system
- a memory layer
- a conversation history manager
- a browser or API tool
- different vector DBs like Pinecone, Weaviate, Qdrant, or pgvector
- a web UI using Streamlit or FastAPI

---

## Notes

This is intentionally minimal. It is designed for understanding, not production deployment.

For a real production system, you would also use:
- auth and access control
- monitoring and logging
- chunking strategies
- re-ranking
- cost controls
- better orchestration logic
