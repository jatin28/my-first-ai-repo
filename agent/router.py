from __future__ import annotations


def is_arithmetic_question(question: str) -> bool:
    q = question.lower()
    arithmetic_tokens = [
        "+", "-", "*", "/", "plus", "minus", "multiply", "divide",
        "sum", "difference", "product", "quotient", "calculate", "math",
        "equation", "compute",
    ]
    if any(token in q for token in arithmetic_tokens):
        return True

    try:
        import ast
        expr = q.replace("^", "**")
        ast.parse(expr, mode="eval")
        return bool(any(ch.isdigit() for ch in q) and any(ch in "+-*/" for ch in q))
    except Exception:
        return False


def is_time_question(question: str) -> bool:
    q = question.lower().strip()
    time_patterns = [
        "what time is it",
        "what time",
        "what date is it",
        "what date",
        "current time",
        "current date",
        "time right now",
        "date today",
        "today's date",
        "what is the time",
        "what is the date",
    ]
    if any(pattern in q for pattern in time_patterns):
        return True

    return q.startswith("time") or q.startswith("date") or q.startswith("what is the time") or q.startswith("what is the date")


def is_weather_question(question: str) -> bool:
    q = question.lower()
    weather_tokens = [
        "weather",
        "forecast",
        "temperature",
        "rain",
        "sunny",
        "cloudy",
        "wind",
        "humidity",
        "storm",
        "snow",
        "cold",
        "hot",
    ]
    return any(token in q for token in weather_tokens)


def route_question(question: str) -> str:
    q = question.lower()
    if is_time_question(question):
        return "tool"
    if is_weather_question(question):
        return "weather"
    if is_arithmetic_question(question):
        return "direct"
    return "retrieve"
