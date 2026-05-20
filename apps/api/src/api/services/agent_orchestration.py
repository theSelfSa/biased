from __future__ import annotations

from typing import Any, Callable

try:
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover - optional dependency
    END = None
    START = None
    StateGraph = None

try:
    from langchain_core.tools import StructuredTool
except Exception:  # pragma: no cover - optional dependency
    StructuredTool = None

QuestionTool = Callable[[str], Any]


def _invoke_tool(
    name: str,
    description: str,
    fn: QuestionTool,
    question: str,
) -> tuple[Any, str]:
    if StructuredTool is None:
        return fn(question), "native"

    tool = StructuredTool.from_function(
        func=fn,
        name=name,
        description=description,
    )
    return tool.invoke({"question": question}), "langchain-core"


def _run_linear(
    state: dict[str, Any],
    safe_sql_tool: QuestionTool,
    rag_tool: QuestionTool,
) -> dict[str, Any]:
    current = dict(state)
    current["route"] = [*current["route"], "router", "sql_analyst"]

    sql_insight, sql_runtime = _invoke_tool(
        "safe_sql_insight",
        "Compute safe, read-only SQL summaries for owner analytics questions.",
        safe_sql_tool,
        current["question"],
    )
    current["sqlInsight"] = str(sql_insight) if sql_insight else None
    current["toolCalls"] = [
        *current["toolCalls"],
        {
            "tool": "safe_sql_insight",
            "status": "used" if sql_insight else "no_result",
            "runtime": sql_runtime,
            "detail": "Generated SQL-backed summary for the current question.",
        },
    ]

    current["route"] = [*current["route"], "rag_retriever"]
    citations, rag_runtime = _invoke_tool(
        "pgvector_rag_lookup",
        "Retrieve nearest business document chunks from pgvector-backed storage.",
        rag_tool,
        current["question"],
    )
    citation_items = (
        list(citations)
        if isinstance(citations, list)
        else ([] if citations is None else [citations])
    )
    current["citations"] = citation_items
    current["toolCalls"] = [
        *current["toolCalls"],
        {
            "tool": "pgvector_rag_lookup",
            "status": "used" if citation_items else "no_result",
            "runtime": rag_runtime,
            "detail": (
                f"Retrieved {len(citation_items)} evidence chunk(s) from pgvector."
            ),
        },
    ]
    current["route"] = [*current["route"], "response_writer"]
    return current


def _run_with_langgraph(
    state: dict[str, Any],
    safe_sql_tool: QuestionTool,
    rag_tool: QuestionTool,
) -> dict[str, Any]:
    if StateGraph is None or START is None or END is None:
        return _run_linear(state, safe_sql_tool, rag_tool)

    graph: Any = StateGraph(dict)

    def router_node(current: dict[str, Any]) -> dict[str, Any]:
        return {**current, "route": [*current["route"], "router"]}

    def sql_agent_node(current: dict[str, Any]) -> dict[str, Any]:
        sql_insight, sql_runtime = _invoke_tool(
            "safe_sql_insight",
            "Compute safe, read-only SQL summaries for owner analytics questions.",
            safe_sql_tool,
            current["question"],
        )
        return {
            **current,
            "route": [*current["route"], "sql_analyst"],
            "sqlInsight": (str(sql_insight) if sql_insight else None),
            "toolCalls": [
                *current["toolCalls"],
                {
                    "tool": "safe_sql_insight",
                    "status": "used" if sql_insight else "no_result",
                    "runtime": sql_runtime,
                    "detail": "Generated SQL-backed summary for the current question.",
                },
            ],
        }

    def rag_agent_node(current: dict[str, Any]) -> dict[str, Any]:
        citations, rag_runtime = _invoke_tool(
            "pgvector_rag_lookup",
            "Retrieve nearest business document chunks from pgvector-backed storage.",
            rag_tool,
            current["question"],
        )
        citation_items = (
            list(citations)
            if isinstance(citations, list)
            else ([] if citations is None else [citations])
        )
        return {
            **current,
            "route": [*current["route"], "rag_retriever"],
            "citations": citation_items,
            "toolCalls": [
                *current["toolCalls"],
                {
                    "tool": "pgvector_rag_lookup",
                    "status": "used" if citation_items else "no_result",
                    "runtime": rag_runtime,
                    "detail": (
                        f"Retrieved {len(citation_items)} evidence chunk(s) from pgvector."
                    ),
                },
            ],
        }

    def writer_node(current: dict[str, Any]) -> dict[str, Any]:
        return {**current, "route": [*current["route"], "response_writer"]}

    graph.add_node("router", router_node)
    graph.add_node("sql_analyst", sql_agent_node)
    graph.add_node("rag_retriever", rag_agent_node)
    graph.add_node("response_writer", writer_node)
    graph.add_edge(START, "router")
    graph.add_edge("router", "sql_analyst")
    graph.add_edge("sql_analyst", "rag_retriever")
    graph.add_edge("rag_retriever", "response_writer")
    graph.add_edge("response_writer", END)
    compiled = graph.compile()
    result = compiled.invoke(state)
    return result if isinstance(result, dict) else state


def orchestrate_investigation(
    *,
    question: str,
    task_class: str,
    provider: str,
    mode: str,
    safe_sql_tool: QuestionTool,
    rag_tool: QuestionTool,
) -> dict[str, Any]:
    base_state: dict[str, Any] = {
        "question": question,
        "taskClass": task_class,
        "provider": provider,
        "mode": mode,
        "route": [],
        "toolCalls": [],
        "toolRuntime": "langchain-core" if StructuredTool is not None else "native",
        "sqlInsight": None,
        "citations": [],
        "framework": "linear-fallback",
    }

    if StateGraph is None or START is None or END is None:
        return _run_linear(base_state, safe_sql_tool, rag_tool)

    try:
        state = _run_with_langgraph(base_state, safe_sql_tool, rag_tool)
        return {
            **state,
            "framework": "langgraph",
        }
    except Exception:
        return _run_linear(base_state, safe_sql_tool, rag_tool)
