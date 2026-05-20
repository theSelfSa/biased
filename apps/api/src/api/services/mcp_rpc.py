from __future__ import annotations

from typing import Any

from api.models import ScenarioPlannerRequest
from api.services.demo_data import (
    build_import_ledger,
    build_scenario_plan,
    build_scheduler_run,
    generate_forecast,
    generate_investigation,
)

JSONRPC_VERSION = "2.0"

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "investigate_business_question",
        "description": (
            "Run the agentic investigation workflow over business memory and return "
            "structured evidence, risks, and recommendations."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["question"],
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Owner-facing business question to investigate.",
                }
            },
        },
    },
    {
        "name": "run_metric_forecast",
        "description": (
            "Generate deterministic forecast bands for sales, purchases, recurring "
            "obligations, or cash."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "default": "sales"},
                "horizon": {
                    "type": "string",
                    "description": "Horizon string like 30d, 45d, or 90d.",
                    "default": "30d",
                },
            },
        },
    },
    {
        "name": "run_scenario_plan",
        "description": (
            "Run multi-hypothesis scenario planning for supplier inflation, "
            "underperforming lines, delayed reorder, or fixed-cost pressure."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["scenarioType"],
            "properties": {
                "scenarioType": {"type": "string"},
                "horizonDays": {"type": "integer", "default": 30},
                "percentage": {"type": "number", "default": 10},
            },
        },
    },
    {
        "name": "run_scheduler",
        "description": (
            "Trigger the daily scheduler path that generates brief, anomaly, and "
            "due-reminder outputs."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_import_ledger",
        "description": "Read import confirmation history and per-collection snapshots.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _jsonrpc_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "result": result,
    }


def _jsonrpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def _invoke_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name == "investigate_business_question":
        question = str(arguments.get("question", "")).strip()
        if not question:
            raise ValueError("question is required")
        return generate_investigation(question)

    if name == "run_metric_forecast":
        metric = str(arguments.get("metric", "sales")).strip() or "sales"
        horizon = str(arguments.get("horizon", "30d")).strip() or "30d"
        return generate_forecast(metric, horizon)

    if name == "run_scenario_plan":
        payload = ScenarioPlannerRequest(**arguments)
        return build_scenario_plan(payload)

    if name == "run_scheduler":
        return build_scheduler_run()

    if name == "read_import_ledger":
        return build_import_ledger()

    raise ValueError(f"unknown tool: {name}")


def handle_mcp_request(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = payload.get("id")
    method = str(payload.get("method", "")).strip()
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        return _jsonrpc_error(request_id, -32602, "params must be an object")

    if method == "initialize":
        return _jsonrpc_result(
            request_id,
            {
                "protocolVersion": "2025-03-26",
                "serverInfo": {
                    "name": "biased-mcp",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    }
                },
            },
        )

    if method == "tools/list":
        return _jsonrpc_result(request_id, {"tools": MCP_TOOLS})

    if method == "tools/call":
        name = str(params.get("name", "")).strip()
        arguments = params.get("arguments") or {}
        if not name:
            return _jsonrpc_error(request_id, -32602, "tool name is required")
        if not isinstance(arguments, dict):
            return _jsonrpc_error(
                request_id,
                -32602,
                "tool arguments must be an object",
            )

        try:
            output = _serialize(_invoke_tool(name, arguments))
        except Exception as exc:
            return _jsonrpc_error(request_id, -32000, str(exc))

        return _jsonrpc_result(
            request_id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool {name} executed successfully.",
                    }
                ],
                "structuredContent": output,
            },
        )

    return _jsonrpc_error(request_id, -32601, f"Unknown method: {method}")
