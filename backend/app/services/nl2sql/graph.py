from typing import Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from app.services.nl2sql.schema import get_schema_profile
from app.services.nl2sql.rules import generate_sql as generate_sql_rules
from app.services.nl2sql.validator import validate_sql
from app.services.nl2sql.repair import repair_sql
from app.services.nl2sql.llm import build_prompt, get_llm_client, parse_llm_output


class NL2SQLState(TypedDict, total=False):
    query: str
    domain: Optional[str]
    schema: Dict[str, List[str]]
    sql: Optional[str]
    questions: List[str]
    error: Optional[str]
    mode: str


def build_graph(db) -> StateGraph:
    def _load_schema(state: NL2SQLState) -> NL2SQLState:
        state["schema"] = get_schema_profile(db)
        return state

    def _generate_sql(state: NL2SQLState) -> NL2SQLState:
        sql, questions, _meta = generate_sql_rules(state["query"], state.get("domain"), state["schema"])
        state["sql"] = sql
        state["questions"] = questions
        return state

    def _generate_sql_llm(state: NL2SQLState) -> NL2SQLState:
        llm = get_llm_client()
        if llm is None:
            return _generate_sql(state)

        prompt = build_prompt(state["query"], state.get("domain"), state["schema"])
        response = llm.invoke(prompt)
        content = response.content.strip() if hasattr(response, "content") else str(response).strip()
        sql, questions = parse_llm_output(content)
        state["sql"] = sql
        state["questions"] = questions
        return state

    def _validate_sql(state: NL2SQLState) -> NL2SQLState:
        sql = state.get("sql")
        if not sql:
            return state
        error = validate_sql(sql)
        if error:
            repaired = repair_sql(sql)
            if repaired:
                sql = repaired
                state["sql"] = sql
                error = validate_sql(sql)
        state["error"] = error
        return state

    def _route_mode(state: NL2SQLState) -> str:
        return "llm" if state.get("mode") == "llm" else "rules"

    graph = StateGraph(NL2SQLState)
    graph.add_node("load_schema", _load_schema)
    graph.add_node("generate_sql", _generate_sql)
    graph.add_node("generate_sql_llm", _generate_sql_llm)
    graph.add_node("validate_sql", _validate_sql)

    graph.set_entry_point("load_schema")
    graph.add_conditional_edges("load_schema", _route_mode, {"rules": "generate_sql", "llm": "generate_sql_llm"})
    graph.add_edge("generate_sql", "validate_sql")
    graph.add_edge("generate_sql_llm", "validate_sql")
    graph.add_edge("validate_sql", END)

    return graph


def run_graph(db, query: str, domain: Optional[str], mode: str) -> NL2SQLState:
    graph = build_graph(db).compile()
    state: NL2SQLState = {"query": query, "domain": domain, "mode": mode}
    return graph.invoke(state)
