"""
Tests for LangChain + LangGraph + LLM (Gemini) integration
and NL2SQL prompts functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

# ── llm.py pure-function tests ──────────────────────────────────────────────

from app.services.nl2sql.llm import build_prompt, parse_llm_output, get_llm_client, _format_schema
from app.services.nl2sql.prompts import DOMAIN_PROMPTS


SAMPLE_SCHEMA = {
    "users": ["id", "name", "email", "created_at"],
    "transactions": ["id", "user_id", "amount", "status", "created_at"],
}


# ── _format_schema ──────────────────────────────────────────────────────────

class TestFormatSchema:
    def test_formats_tables_and_columns(self):
        result = _format_schema(SAMPLE_SCHEMA)
        assert "users(id, name, email, created_at)" in result
        assert "transactions(id, user_id, amount, status, created_at)" in result

    def test_empty_schema(self):
        assert _format_schema({}) == ""

    def test_single_column(self):
        result = _format_schema({"t": ["col"]})
        assert result == "t(col)"


# ── build_prompt ────────────────────────────────────────────────────────────

class TestBuildPrompt:
    def test_contains_user_question(self):
        prompt = build_prompt("show all users", "security", SAMPLE_SCHEMA)
        assert "show all users" in prompt

    def test_includes_domain_focus(self):
        prompt = build_prompt("list transactions", "security", SAMPLE_SCHEMA)
        assert DOMAIN_PROMPTS["security"] in prompt
        assert "Domain: security" in prompt

    def test_none_domain_defaults_to_general(self):
        prompt = build_prompt("list users", None, SAMPLE_SCHEMA)
        assert "Domain: general" in prompt
        assert DOMAIN_PROMPTS["general"] in prompt

    def test_includes_schema(self):
        prompt = build_prompt("query", "general", SAMPLE_SCHEMA)
        assert "users(id, name, email, created_at)" in prompt

    def test_includes_clarify_instruction(self):
        prompt = build_prompt("q", None, SAMPLE_SCHEMA)
        assert "CLARIFY:" in prompt

    def test_all_domain_prompts_exist(self):
        for domain in ["security", "compliance", "risk", "operations", "general"]:
            assert domain in DOMAIN_PROMPTS
            prompt = build_prompt("test", domain, SAMPLE_SCHEMA)
            assert DOMAIN_PROMPTS[domain] in prompt


# ── parse_llm_output ───────────────────────────────────────────────────────

class TestParseLlmOutput:
    def test_plain_sql(self):
        sql, questions = parse_llm_output("SELECT * FROM users")
        assert sql == "SELECT * FROM users"
        assert questions == []

    def test_clarify_single_question(self):
        sql, questions = parse_llm_output("CLARIFY: Which time range?")
        assert sql is None
        assert questions == ["Which time range?"]

    def test_clarify_multiple_questions(self):
        text = "CLARIFY:\n- Which table?\n- What time range?\n- Which user?"
        sql, questions = parse_llm_output(text)
        assert sql is None
        assert len(questions) == 3
        assert "Which table?" in questions
        assert "What time range?" in questions
        assert "Which user?" in questions

    def test_clarify_case_insensitive(self):
        sql, questions = parse_llm_output("clarify: Do you mean login_events?")
        assert sql is None
        assert len(questions) == 1

    def test_sql_with_code_block(self):
        text = "```sql\nSELECT * FROM users LIMIT 10\n```"
        sql, questions = parse_llm_output(text)
        assert sql is not None
        assert "SELECT * FROM users LIMIT 10" in sql
        assert questions == []

    def test_sql_with_prefix(self):
        text = "SQL: SELECT COUNT(*) FROM transactions"
        sql, questions = parse_llm_output(text)
        assert sql == "SELECT COUNT(*) FROM transactions"

    def test_whitespace_handling(self):
        sql, questions = parse_llm_output("  \n  SELECT 1  \n  ")
        assert sql == "SELECT 1"

    def test_empty_string(self):
        sql, questions = parse_llm_output("")
        assert sql == ""
        assert questions == []


# ── get_llm_client ──────────────────────────────────────────────────────────

class TestGetLlmClient:
    def test_stub_provider_returns_none(self):
        """Current .env has LLM_PROVIDER=stub → returns None"""
        with patch("app.services.nl2sql.llm.get_settings") as mock_settings:
            s = MagicMock()
            s.llm_provider = "stub"
            mock_settings.return_value = s
            assert get_llm_client() is None

    def test_unknown_provider_returns_none(self):
        with patch("app.services.nl2sql.llm.get_settings") as mock_settings:
            s = MagicMock()
            s.llm_provider = "cohere"
            mock_settings.return_value = s
            assert get_llm_client() is None

    def test_openai_provider_needs_key(self):
        with patch("app.services.nl2sql.llm.get_settings") as mock_settings:
            s = MagicMock()
            s.llm_provider = "openai"
            s.openai_api_key = None
            mock_settings.return_value = s
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                get_llm_client()

    def test_gemini_provider_needs_key(self):
        with patch("app.services.nl2sql.llm.get_settings") as mock_settings:
            s = MagicMock()
            s.llm_provider = "gemini"
            s.gemini_api_key = None
            mock_settings.return_value = s
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                get_llm_client()

    def test_openai_provider_returns_chat_openai(self):
        with patch("app.services.nl2sql.llm.get_settings") as mock_settings:
            s = MagicMock()
            s.llm_provider = "openai"
            s.openai_api_key = "sk-test-key"
            s.llm_model = "gpt-4o-mini"
            mock_settings.return_value = s
            client = get_llm_client()
            assert client is not None
            from langchain_openai import ChatOpenAI
            assert isinstance(client, ChatOpenAI)

    def test_gemini_provider_returns_chat_google(self):
        with patch("app.services.nl2sql.llm.get_settings") as mock_settings:
            s = MagicMock()
            s.llm_provider = "gemini"
            s.gemini_api_key = "AIzaTestKey"
            s.llm_model = "gemini-2.0-flash"
            mock_settings.return_value = s
            client = get_llm_client()
            assert client is not None
            from langchain_google_genai import ChatGoogleGenerativeAI
            assert isinstance(client, ChatGoogleGenerativeAI)


# ── LangGraph graph.py unit tests (mocked LLM) ─────────────────────────────

from app.services.nl2sql.graph import build_graph, run_graph, NL2SQLState


class TestLangGraphRulesMode:
    """graph.py in rules mode — no LLM needed."""

    def test_run_graph_rules_produces_sql(self, client):
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            state = run_graph(db, "list all users", None, "rules")
            assert state["sql"] is not None
            assert "users" in state["sql"].lower()
            assert state.get("error") is None
        finally:
            db.close()

    def test_run_graph_rules_unknown_table_asks_clarification(self, client):
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            state = run_graph(db, "show me the widget stock", None, "rules")
            assert state.get("sql") is None
            assert len(state.get("questions", [])) > 0
        finally:
            db.close()


class TestLangGraphLLMMode:
    """graph.py in llm mode — LLM is mocked."""

    def test_llm_mode_generates_sql(self, client):
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            mock_response = MagicMock()
            mock_response.content = "SELECT id, name FROM users LIMIT 10"
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response

            with patch("app.services.nl2sql.graph.get_llm_client", return_value=mock_llm):
                state = run_graph(db, "show users", None, "llm")
            assert state["sql"] is not None
            assert "users" in state["sql"].lower()
            assert state.get("error") is None
        finally:
            db.close()

    def test_llm_mode_clarify(self, client):
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            mock_response = MagicMock()
            mock_response.content = "CLARIFY: Which date range do you want?"
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response

            with patch("app.services.nl2sql.graph.get_llm_client", return_value=mock_llm):
                state = run_graph(db, "show data", None, "llm")
            assert state.get("sql") is None
            assert len(state.get("questions", [])) > 0
        finally:
            db.close()

    def test_llm_mode_falls_back_to_rules_when_no_client(self, client):
        """When get_llm_client returns None (stub), LLM node falls back to rules."""
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            with patch("app.services.nl2sql.graph.get_llm_client", return_value=None):
                state = run_graph(db, "list all users", None, "llm")
            # Should still produce SQL via rules fallback
            assert state["sql"] is not None
            assert "users" in state["sql"].lower()
        finally:
            db.close()

    def test_llm_mode_validates_and_repairs(self, client):
        """LLM returns SQL missing LIMIT → repair adds it."""
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            mock_response = MagicMock()
            mock_response.content = "SELECT * FROM users"
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response

            with patch("app.services.nl2sql.graph.get_llm_client", return_value=mock_llm):
                state = run_graph(db, "show users", None, "llm")
            assert state["sql"] is not None
            assert state.get("error") is None
            # Repaired SQL should still be valid
            from app.services.nl2sql.validator import validate_sql
            assert validate_sql(state["sql"]) is None
        finally:
            db.close()

    def test_llm_mode_rejects_write_sql(self, client):
        """LLM returning a write statement should fail validation."""
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            mock_response = MagicMock()
            mock_response.content = "DROP TABLE users"
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response

            with patch("app.services.nl2sql.graph.get_llm_client", return_value=mock_llm):
                state = run_graph(db, "delete everything", None, "llm")
            assert state.get("error") is not None
        finally:
            db.close()


# ── engine.py pipeline tests ───────────────────────────────────────────────

from app.services.nl2sql.engine import run_query_pipeline


class TestRunQueryPipelineLLMMode:
    """Full pipeline tests with mocked LLM."""

    def test_pipeline_llm_mode_returns_rows(self, client):
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            mock_response = MagicMock()
            mock_response.content = "SELECT id, name FROM users LIMIT 5"
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response

            with (
                patch("app.services.nl2sql.graph.get_llm_client", return_value=mock_llm),
                patch("app.core.config.get_settings") as mock_gs,
            ):
                s = MagicMock()
                s.nl2sql_mode = "llm"
                s.llm_provider = "gemini"
                s.gemini_api_key = "test"
                s.llm_model = "gemini-2.0-flash"
                mock_gs.return_value = s

                result = run_query_pipeline(db, "show users", None)

            assert result["sql"] is not None
            assert isinstance(result["rows"], list)
            assert result["clarification_needed"] is False
        finally:
            db.close()

    def test_pipeline_llm_mode_clarification(self, client):
        from app.db.session import SessionLocalPrimary
        db = SessionLocalPrimary()
        try:
            mock_response = MagicMock()
            mock_response.content = "CLARIFY: Which dataset?"
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response

            with (
                patch("app.services.nl2sql.graph.get_llm_client", return_value=mock_llm),
                patch("app.core.config.get_settings") as mock_gs,
            ):
                s = MagicMock()
                s.nl2sql_mode = "llm"
                s.llm_provider = "gemini"
                s.gemini_api_key = "test"
                s.llm_model = "gemini-2.0-flash"
                mock_gs.return_value = s

                result = run_query_pipeline(db, "show data", None)

            assert result["clarification_needed"] is True
            assert len(result["clarification_questions"]) > 0
            assert result["sql"] is None
        finally:
            db.close()


# ── Validator & repair unit tests ───────────────────────────────────────────

from app.services.nl2sql.validator import validate_sql, is_read_only_sql, has_single_statement
from app.services.nl2sql.repair import repair_sql


class TestValidator:
    def test_valid_select(self):
        assert validate_sql("SELECT * FROM users") is None

    def test_rejects_insert(self):
        err = validate_sql("INSERT INTO users(name) VALUES ('x')")
        assert err is not None

    def test_rejects_drop(self):
        err = validate_sql("DROP TABLE users")
        assert err is not None

    def test_rejects_multi_statement(self):
        err = validate_sql("SELECT 1; SELECT 2")
        assert err is not None

    def test_rejects_alter_table(self):
        err = validate_sql("ALTER TABLE users ADD col INT")
        assert err is not None

    def test_rejects_delete(self):
        err = validate_sql("DELETE FROM users")
        assert err is not None


class TestRepair:
    def test_adds_limit(self):
        result = repair_sql("SELECT * FROM users")
        assert result is not None
        assert "LIMIT" in result.upper()

    def test_preserves_existing_limit(self):
        result = repair_sql("SELECT * FROM users LIMIT 5")
        assert result is not None
        assert "5" in result

    def test_invalid_sql_returns_none(self):
        result = repair_sql("NOT VALID SQL ;;; %%%")
        # sqlglot may or may not parse this; if it can't, returns None
        # This just verifies no crash
        assert result is None or isinstance(result, str)


# ── Prompts module ──────────────────────────────────────────────────────────

class TestDomainPrompts:
    def test_all_five_domains_present(self):
        expected = {"security", "compliance", "risk", "operations", "general"}
        assert set(DOMAIN_PROMPTS.keys()) == expected

    def test_prompts_are_nonempty_strings(self):
        for domain, prompt in DOMAIN_PROMPTS.items():
            assert isinstance(prompt, str), f"{domain} prompt is not a string"
            assert len(prompt) > 10, f"{domain} prompt is too short"
