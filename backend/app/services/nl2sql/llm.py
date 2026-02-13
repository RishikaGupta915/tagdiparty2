from typing import Any, Dict, List, Tuple, Optional
from app.core.config import get_settings
from app.services.nl2sql.prompts import DOMAIN_PROMPTS


def _format_schema(schema: Dict[str, List[str]]) -> str:
    lines = []
    for table, columns in schema.items():
        cols = ", ".join(columns)
        lines.append(f"{table}({cols})")
    return "\n".join(lines)


def build_prompt(query: str, domain: str | None, schema: Dict[str, List[str]]) -> str:
    schema_text = _format_schema(schema)
    domain_text = domain or "general"
    domain_prompt = DOMAIN_PROMPTS.get(domain_text, DOMAIN_PROMPTS["general"])
    return (
        "You are a SQL generator. Use only the tables and columns provided. "
        "Return a single SELECT statement and nothing else. "
        "If the request is ambiguous, respond with:\n"
        "CLARIFY: <one or more short questions>\n"
        f"Domain: {domain_text}\n"
        f"Domain focus: {domain_prompt}\n"
        f"Schema:\n{schema_text}\n"
        f"User question: {query}\n"
    )


def parse_llm_output(text: str) -> Tuple[Optional[str], List[str]]:
    cleaned = text.strip()
    if cleaned.lower().startswith("clarify:"):
        questions = cleaned.split(":", 1)[1].strip()
        question_list = [q.strip("- ").strip() for q in questions.splitlines() if q.strip()]
        if not question_list and questions:
            question_list = [questions]
        return None, question_list
    if cleaned.lower().startswith("sql:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("sql", "", 1).strip()
    return cleaned.strip(), []


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
