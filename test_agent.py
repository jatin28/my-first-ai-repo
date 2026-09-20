import unittest

from agent import SimpleRAGAgent
from agent.router import route_question


class TestSimpleRAGAgent(unittest.TestCase):
    def test_prompt_uses_context_and_reasoning_rather_than_refusing(self):
        agent = SimpleRAGAgent()
        prompt = agent._build_prompt(
            "Who is the president of France?",
            "Memory, RAG, and Embedding Model are discussed here.",
            [],
        )

        self.assertIn("Use the retrieved context first", prompt)
        self.assertIn("If the context is missing or only partly relevant", prompt)
        self.assertIn("answer using your best reasoning", prompt)

    def test_fallback_answer_does_not_forbid_general_reasoning(self):
        agent = SimpleRAGAgent()
        fallback = agent._fallback_answer(
            "Who is the president of France?",
            [{"content": "Memory, RAG, and Embedding Model are discussed here."}],
        )

        self.assertIn("general knowledge", fallback.lower())
        self.assertNotIn("context only provides", fallback.lower())

    def test_arithmetic_question_ignores_irrelevant_history_and_trims_memory(self):
        agent = SimpleRAGAgent()
        self.assertTrue(agent._is_arithmetic_question("What is 2 + 2?"))
        self.assertTrue(agent._is_arithmetic_question("calculate 9 * 7"))

        history = [
            {"role": "user", "content": "Who is the president of France?"},
            {"role": "assistant", "content": "Emmanuel Macron."},
            {"role": "user", "content": "What is RAG?"},
            {"role": "assistant", "content": "Retrieval augmented generation."},
            {"role": "user", "content": "What is memory?"},
            {"role": "assistant", "content": "It stores context."},
        ]

        trimmed = agent._trim_history(history, max_turns=2)
        self.assertEqual(len(trimmed), 4)
        self.assertTrue(any(item["content"] == "What is memory?" for item in trimmed))
        self.assertTrue(any(item["content"] == "It stores context." for item in trimmed))

        filtered = agent._filter_history_for_question(history, "2 + 2")
        self.assertEqual(filtered, [])

    def test_weather_today_is_not_routed_as_time(self):
        self.assertNotEqual(route_question("what is weather today"), "tool")
        self.assertEqual(route_question("what time is it"), "tool")
        self.assertEqual(route_question("what is the date today"), "tool")


if __name__ == "__main__":
    unittest.main()
