# Hugging Face Spaces deployment

This folder is prepared for a Gradio or Streamlit deployment.

## Option A: Streamlit

Create a new app with a `requirements.txt` file and a `app.py` entrypoint.

## Option B: Gradio

Use the same pattern with a Gradio app.

This project is currently organized as a FastAPI backend plus React frontend for local learning.

For Hugging Face Spaces, a simpler deployable version would be a single Python file that wraps your agent and exposes a small chat UI.
