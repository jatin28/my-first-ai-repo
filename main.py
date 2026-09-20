from agent import SimpleRAGAgent


def main() -> None:
    agent = SimpleRAGAgent()

    sample_questions = [
        "What is an AI agent?",
        "What is RAG?",
        "How does a vector database help search?",
        "What is the difference between a prompt and retrieval?",
    ]

    for question in sample_questions:
        print(f"Q: {question}")
        print("A:")
        print(agent.ask(question))
        print("-" * 80)


if __name__ == "__main__":
    main()
