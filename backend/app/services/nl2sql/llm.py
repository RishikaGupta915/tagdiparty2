from typing import Any, Dict, List
from app.core.config import get_settings


def _format_schema(schema: Dict[str, List[str]]) -> str:
    lines = []
    for table, columns in schema.items():
        cols = ", ".join(columns)
        lines.append(f"{table}({cols})")
    return "\n".join(lines)


def build_prompt(query: str, domain: str | None, schema: Dict[str, List[str]]) -> str:
    schema_text = _format_schema(schema)
    domain_text = domain or "general"
    return (
        "You are a SQL generator. Use only the tables and columns provided. "
        "Return a single SELECT statement and nothing else.\n"
        f"Domain: {domain_text}\n"
        f"Schema:\n{schema_text}\n"
        f"User question: {query}\n"
    )


def get_llm_client():
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for openai provider")
        return ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key, temperature=0)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for gemini provider")
        return ChatGoogleGenerativeAI(model=settings.llm_model, google_api_key=settings.gemini_api_key, temperature=0)

    return None
