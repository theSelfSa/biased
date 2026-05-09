from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb
import openpyxl
import polars as pl

from api.models import (
    ActionDraft,
    ActionCenterItem,
    ActionCenterSnapshot,
    BriefingResult,
    BusinessDocument,
    CreateRecurringObligationRequest,
    ImportCollectionSummary,
    ImportConfirmResponse,
    ImportHistoryEntry,
    ImportLedgerSnapshot,
    ImportPreview,
    InvestigationResult,
    RecurringObligation,
)


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "data" / "demo").exists():
            return parent
    raise RuntimeError("Unable to locate repository root for demo data.")


DEMO_DIR = repo_root() / "data" / "demo"
RUNTIME_DIR = DEMO_DIR / "runtime"

REQUIRED_FIELDS: dict[str, set[str]] = {
    "sales": {"date", "sku", "amount_inr"},
    "purchases": {"date", "supplier_name", "sku", "amount_inr"},
    "products": {"sku", "name", "category", "quantity_on_hand"},
    "expenses": {"occurred_on", "label", "category", "amount_inr"},
    "recurring_obligations": {"label", "category", "amount_inr", "due_date", "recurrence"},
}

IMPORT_RECORD_TYPES = ["sales", "purchases", "products", "expenses", "recurring_obligations"]


def load_json(name: str):
    return json.loads((DEMO_DIR / name).read_text(encoding="utf-8"))


def runtime_path(name: str) -> Path:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR / name


def load_runtime_json(name: str, default_factory):
    path = runtime_path(name)
    if not path.exists():
        payload = default_factory()
        save_runtime_json(name, payload)
        return payload
    return json.loads(path.read_text(encoding="utf-8"))


def save_runtime_json(name: str, payload: Any) -> None:
    runtime_path(name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_inr_short(amount: float) -> str:
    if amount >= 100000:
        return f"₹{amount / 100000:.2f}L"
    if amount >= 1000:
        return f"₹{amount / 1000:.1f}K"
    return f"₹{amount:,.0f}"


def normalize_status(value: str | None) -> str:
    if value in {"due", "paid", "scheduled"}:
        return value
    return "scheduled"


def normalize_recurrence(value: str | None) -> str:
    if value in {"monthly", "quarterly", "annual"}:
        return value
    return "monthly"


def sort_obligations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {"due": 0, "scheduled": 1, "paid": 2}
    return sorted(
        items,
        key=lambda item: (
            order.get(item.get("status", "scheduled"), 1),
            item.get("dueDate", "9999-12-31"),
            item.get("label", ""),
        ),
    )


def dashboard_seed() -> dict[str, Any]:
    return load_json("pharmacy-dashboard.json")


def obligations_seed() -> list[dict[str, Any]]:
    return dashboard_seed()["obligations"]


def load_recurring_obligations() -> list[dict[str, Any]]:
    payload = load_runtime_json("recurring-obligations.json", obligations_seed)
    normalized = [
        RecurringObligation(
            id=item["id"],
            label=item["label"],
            category=item["category"],
            amountInr=float(item["amountInr"]),
            dueDate=item["dueDate"],
            recurrence=normalize_recurrence(item.get("recurrence")),
            status=normalize_status(item.get("status")),
        ).model_dump()
        for item in payload
    ]
    normalized = sort_obligations(normalized)
    save_runtime_json("recurring-obligations.json", normalized)
    return normalized


def save_recurring_obligations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = sort_obligations(
        [
            RecurringObligation(
                id=item["id"],
                label=item["label"],
                category=item["category"],
                amountInr=float(item["amountInr"]),
                dueDate=item["dueDate"],
                recurrence=normalize_recurrence(item.get("recurrence")),
                status=normalize_status(item.get("status")),
            ).model_dump()
            for item in items
        ]
    )
    save_runtime_json("recurring-obligations.json", normalized)
    return normalized


def documents_seed() -> list[dict[str, Any]]:
    return load_json("pharmacy-documents.json")


def load_documents() -> list[dict[str, Any]]:
    payload = load_runtime_json("documents.json", documents_seed)
    documents = [BusinessDocument(**item).model_dump() for item in payload]
    return sorted(documents, key=lambda item: item["uploadedAt"], reverse=True)


def save_documents(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents = [BusinessDocument(**item).model_dump() for item in items]
    save_runtime_json("documents.json", documents)
    return documents


def import_jobs_seed() -> dict[str, Any]:
    return {}


def import_records_seed() -> dict[str, Any]:
    return {
        "history": [],
        "sales": [],
        "purchases": [],
        "products": [],
        "expenses": [],
        "recurring_obligations": [],
    }


def load_import_jobs() -> dict[str, Any]:
    return load_runtime_json("import-jobs.json", import_jobs_seed)


def save_import_jobs(payload: dict[str, Any]) -> None:
    save_runtime_json("import-jobs.json", payload)


def load_import_records() -> dict[str, Any]:
    payload = load_runtime_json("import-records.json", import_records_seed)
    for key in ["history", *IMPORT_RECORD_TYPES]:
        payload.setdefault(key, [])
    return payload


def save_import_records(payload: dict[str, Any]) -> None:
    save_runtime_json("import-records.json", payload)


def latest_history_for_type(history: list[dict[str, Any]], import_type: str) -> str | None:
    for item in history:
        if item["importType"] == import_type:
            return str(item["confirmedAt"])
    return None


def columns_for_rows(rows: list[dict[str, Any]]) -> list[str]:
    columns: set[str] = set()
    for row in rows:
        columns.update(row.keys())
    return sorted(columns)


def build_import_ledger() -> ImportLedgerSnapshot:
    import_records = load_import_records()
    history = sorted(
        import_records["history"],
        key=lambda item: item["confirmedAt"],
        reverse=True,
    )
    collections = []

    for import_type in IMPORT_RECORD_TYPES:
        rows = import_records.get(import_type, [])
        sample_rows = list(reversed(rows[-3:]))
        collections.append(
            ImportCollectionSummary(
                importType=import_type,
                rowCount=len(rows),
                latestImportAt=latest_history_for_type(history, import_type),
                columns=columns_for_rows(rows),
                sampleRows=sample_rows,
            )
        )

    return ImportLedgerSnapshot(
        history=[ImportHistoryEntry(**item) for item in history],
        collections=collections,
    )


def format_action_amount(item: dict[str, Any]) -> str:
    return f"₹{float(item['amountInr']):,.0f}"


def days_until_due(item: dict[str, Any]) -> int:
    return (parse_iso_date(item["dueDate"]) - date.today()).days


def build_action_queue() -> ActionCenterSnapshot:
    obligations = load_recurring_obligations()
    import_ledger = build_import_ledger()
    queue: list[ActionCenterItem] = []

    unpaid = [item for item in obligations if item["status"] != "paid"]
    due_soon = sorted(unpaid, key=days_until_due)

    for item in due_soon[:3]:
        days = days_until_due(item)
        is_supplier = item["category"].lower() == "supplier"
        if is_supplier:
            queue.append(
                ActionCenterItem(
                    id=f"draft-{item['id']}",
                    title=f"Stage supplier follow-up for {item['label']}",
                    detail=(
                        f"{format_action_amount(item)} is due on {item['dueDate']}. "
                        "Prepare a message before the next payment cycle tightens cash."
                    ),
                    severity="critical" if days <= 3 else "warning",
                    actionType="vendor_follow_up",
                    targetEntity=item["label"],
                    status="open",
                )
            )
            continue

        queue.append(
            ActionCenterItem(
                id=f"obligation-{item['id']}",
                title=f"Protect cash for {item['label']}",
                detail=(
                    f"{format_action_amount(item)} is {('overdue' if days < 0 else f'due in {days} days')} "
                    "and should stay visible in the owner plan."
                ),
                severity="critical" if days <= 2 else "warning",
                actionType="bill_review",
                targetEntity=item["label"],
                status="open",
            )
        )

    for entry in import_ledger.history[:2]:
        queue.append(
            ActionCenterItem(
                id=f"import-{entry.jobId}",
                title=f"Review the latest {entry.importType.replace('_', ' ')} import",
                detail=(
                    f"{entry.appliedCount} rows from {entry.filename} were added on "
                    f"{entry.confirmedAt[:10]}. Use this ledger in your next investigation."
                ),
                severity="info",
                actionType="review_import",
                targetEntity=entry.importType,
                status="watching",
            )
        )

    if not queue:
        base_actions = dashboard_seed()["actionQueue"]
        queue = [
            ActionCenterItem(
                id=item["id"],
                title=item["title"],
                detail=item["detail"],
                severity=item["severity"],
                actionType="watchlist",
                targetEntity=item["title"],
                status="watching",
            )
            for item in base_actions
        ]

    headline = (
        "Focus first on obligations that can tighten cash, then use the imported ledgers "
        "to validate what changed most recently."
    )
    return ActionCenterSnapshot(headline=headline, items=queue)


def load_dashboard() -> dict[str, Any]:
    payload = dashboard_seed()
    obligations = load_recurring_obligations()
    actions = build_action_queue()
    due_soon = [
        item
        for item in obligations
        if item["status"] != "paid"
        and 0 <= (parse_iso_date(item["dueDate"]) - date.today()).days <= 10
    ]
    total_due_soon = sum(float(item["amountInr"]) for item in due_soon)
    due_labels = ", ".join(item["label"] for item in due_soon[:3]) or "No recurring bills due soon"

    payload["obligations"] = obligations
    payload["actionQueue"] = [item.model_dump() for item in actions.items[:4]]
    payload["stats"][2]["value"] = format_inr_short(total_due_soon)
    payload["stats"][2]["delta"] = due_labels
    payload["stats"][2]["tone"] = "critical" if total_due_soon else "neutral"
    return payload


def load_duckdb() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect()
    expenses_path = (DEMO_DIR / "pharmacy-expenses.csv").as_posix()
    recurring_path = (DEMO_DIR / "pharmacy-recurring-obligations.csv").as_posix()
    products_path = (DEMO_DIR / "pharmacy-products.csv").as_posix()
    conn.execute(
        f"create or replace temp view expenses as select * from read_csv_auto('{expenses_path}')"
    )
    conn.execute(
        f"create or replace temp view recurring_obligations as select * from read_csv_auto('{recurring_path}')"
    )
    conn.execute(
        f"create or replace temp view products as select * from read_csv_auto('{products_path}')"
    )
    return conn


def generate_briefing() -> BriefingResult:
    obligations = load_recurring_obligations()
    due_today = [
        f"{item['label']} — ₹{float(item['amountInr']):,.0f}"
        for item in obligations
        if item["status"] != "paid" and item["dueDate"] <= date.today().isoformat()
    ]
    payload = load_json("pharmacy-briefing.json")
    payload["dueToday"] = due_today or payload["dueToday"]
    return BriefingResult(**payload)


def generate_investigation(question: str) -> InvestigationResult:
    conn = load_duckdb()
    utility_avg = conn.execute(
        "select round(avg(amount_inr), 2) from expenses where category = 'Utilities'"
    ).fetchone()[0]
    upcoming_supplier = conn.execute(
        "select max(amount_inr) from recurring_obligations where category = 'Supplier'"
    ).fetchone()[0]
    near_expiry = conn.execute(
        "select count(*) from products where expires_on <= '2026-06-30'"
    ).fetchone()[0]
    conn.close()

    payload = load_json("pharmacy-investigation.json")
    payload["question"] = question
    payload["evidence"][0]["detail"] = (
        f"Average utility burden is ₹{utility_avg:,.0f}, with the latest cycle materially higher due to cooling demand."
    )
    payload["evidence"][1]["detail"] = (
        f"₹{upcoming_supplier:,.0f} is the largest upcoming supplier obligation in the current cycle."
    )
    payload["evidence"][2]["detail"] = (
        f"{near_expiry} product lots fall inside the near-expiry watch window for the next 45 days."
    )
    return InvestigationResult(**payload)


def generate_forecast(metric: str, horizon: str):
    return {
        "metric": metric,
        "horizon": horizon,
        "baseline": "Recent weekly sales average: ₹1.98L",
        "projectedRange": "₹1.9L - ₹2.18L per week",
        "assumptions": [
            "Weekend OTC demand remains elevated",
            "No major supplier disruption hits the next cycle",
            "Fast-moving fever and pain SKUs continue at the current pace",
        ],
        "warnings": [
            "Gross margin stays under pressure if utility costs remain elevated",
            "Slow dermatology stock should not be reordered at the same cadence",
        ],
    }


def draft_action(action_id: str) -> ActionDraft:
    action_queue = build_action_queue().items
    item = next((entry for entry in action_queue if entry.id == action_id), None)
    if item is None:
        item = next((entry for entry in action_queue if entry.actionType == "vendor_follow_up"), None)

    if item is None:
        item = ActionCenterItem(
            id="fallback-action",
            title="Review the current action queue",
            detail="No runtime action was found, so this draft falls back to the current default guidance.",
            severity="info",
            actionType="review_import",
            targetEntity="Current workspace",
            status="watching",
        )

    if item.actionType == "bill_review":
        return ActionDraft(
            actionType=item.actionType,
            targetEntity=item.targetEntity,
            rationale="Recurring operating costs need a clear owner check before they land together.",
            draftText=(
                f"Review {item.targetEntity} today, confirm the due amount, and decide whether "
                "it should be paid now, deferred, or offset by delaying a discretionary purchase."
            ),
            approvalRequired=True,
        )

    if item.actionType == "review_import":
        return ActionDraft(
            actionType=item.actionType,
            targetEntity=item.targetEntity,
            rationale="Freshly imported records are only useful once the owner validates what changed.",
            draftText=(
                f"Open the {item.targetEntity.replace('_', ' ')} ledger, verify the most recent rows, "
                "and use the updated history in the next margin or cash-flow investigation."
            ),
            approvalRequired=False,
        )

    return ActionDraft(
        actionType=item.actionType,
        targetEntity=item.targetEntity,
        rationale="Short-term cash preservation is better than carrying more slow inventory.",
        draftText=(
            "Hello, we would like to stagger the next settlement and trim the dermatology "
            "reorder size for this cycle while we move the current inventory first."
        ),
        approvalRequired=True,
    )


def read_tabular_upload(filename: str, content: bytes) -> pl.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return pl.read_csv(io.BytesIO(content))

    if suffix in {".xlsx", ".xlsm"}:
        workbook = openpyxl.load_workbook(
            io.BytesIO(content), data_only=True, read_only=True
        )
        sheet = workbook.active
        rows = list(sheet.values)
        workbook.close()
        headers = [str(value) for value in rows[0]]
        records = [dict(zip(headers, row, strict=False)) for row in rows[1:]]
        return pl.DataFrame(records)

    raise ValueError("Only CSV and Excel files are supported in the current preview flow.")


def preview_upload(import_type: str, filename: str, content: bytes) -> tuple[ImportPreview, list[dict[str, Any]]]:
    frame = read_tabular_upload(filename, content)
    inferred = infer_mappings(import_type, [str(column) for column in frame.columns])

    warnings: list[str] = []
    manual_review = [source for source, target in inferred.items() if target == "review_manually"]
    if manual_review:
        warnings.append(
            "Some columns need manual review: " + ", ".join(sorted(manual_review))
        )

    required_fields = REQUIRED_FIELDS.get(import_type, set())
    missing_fields = sorted(required_fields.difference(inferred.values()))
    if missing_fields:
        warnings.append(
            "Missing canonical mappings: " + ", ".join(missing_fields)
        )

    preview = ImportPreview(
        importType=import_type,
        filename=filename,
        rowCount=frame.height,
        columns=[str(column) for column in frame.columns],
        inferredMappings=inferred,
        warnings=warnings,
    )
    normalized_rows = normalize_rows(frame, inferred)
    return preview, normalized_rows


def infer_mappings(import_type: str, columns: list[str]) -> dict[str, str]:
    aliases = {
        "sales": {
            "date": "date",
            "sku": "sku",
            "product_name": "name",
            "category": "category",
            "qty": "quantity",
            "revenue_inr": "amount_inr",
            "margin_pct": "margin_pct",
        },
        "purchases": {
            "date": "date",
            "supplier": "supplier_name",
            "sku": "sku",
            "quantity": "quantity",
            "amount_inr": "amount_inr",
        },
        "products": {
            "sku": "sku",
            "name": "name",
            "category": "category",
            "unit_price_inr": "unit_price_inr",
            "quantity_on_hand": "quantity_on_hand",
            "expires_on": "expires_on",
        },
        "expenses": {
            "date": "occurred_on",
            "label": "label",
            "category": "category",
            "amount_inr": "amount_inr",
        },
        "recurring_obligations": {
            "label": "label",
            "category": "category",
            "amount_inr": "amount_inr",
            "due_date": "due_date",
            "recurrence": "recurrence",
            "status": "status",
        },
    }
    normalized = {column: column.strip().lower().replace(" ", "_") for column in columns}
    mapping = aliases.get(import_type, {})
    return {
        source: mapping.get(alias, "review_manually") for source, alias in normalized.items()
    }


def coerce_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 2)
    if hasattr(value, "item"):
        return value.item()
    return value


def normalize_rows(frame: pl.DataFrame, inferred: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in frame.to_dicts():
        normalized: dict[str, Any] = {}
        for source, target in inferred.items():
            if target == "review_manually":
                continue
            raw_value = row.get(source)
            coerced = coerce_json_value(raw_value)
            if coerced is None or coerced == "":
                continue
            normalized[target] = coerced
        if normalized:
            records.append(normalized)
    return records


def store_import_job(preview: ImportPreview, rows: list[dict[str, Any]]) -> str:
    job_id = str(uuid.uuid4())
    jobs = load_import_jobs()
    jobs[job_id] = {
        "preview": preview.model_dump(),
        "rows": rows,
        "confirmed": False,
        "appliedCount": 0,
    }
    save_import_jobs(jobs)
    return job_id


def create_recurring_obligation(
    payload: CreateRecurringObligationRequest,
) -> RecurringObligation:
    obligations = load_recurring_obligations()
    obligation = RecurringObligation(
        id=f"obl-{uuid.uuid4().hex[:8]}",
        label=payload.label.strip(),
        category=payload.category.strip(),
        amountInr=round(float(payload.amountInr), 2),
        dueDate=payload.dueDate,
        recurrence=normalize_recurrence(payload.recurrence),
        status=normalize_status(payload.status),
    )
    obligations.append(obligation.model_dump())
    save_recurring_obligations(obligations)
    return obligation


def mark_recurring_obligation_status(
    obligation_id: str, status: str
) -> RecurringObligation | None:
    obligations = load_recurring_obligations()
    updated: RecurringObligation | None = None
    for item in obligations:
        if item["id"] != obligation_id:
            continue
        item["status"] = normalize_status(status)
        updated = RecurringObligation(**item)
        break

    if updated is None:
        return None

    save_recurring_obligations(obligations)
    return updated


def build_imported_obligation(row: dict[str, Any]) -> RecurringObligation:
    return RecurringObligation(
        id=f"obl-{uuid.uuid4().hex[:8]}",
        label=str(row.get("label", "Imported obligation")),
        category=str(row.get("category", "Operations")),
        amountInr=round(float(row.get("amount_inr", 0)), 2),
        dueDate=str(row.get("due_date", date.today().isoformat())),
        recurrence=normalize_recurrence(str(row.get("recurrence", "monthly"))),
        status=normalize_status(str(row.get("status", "scheduled"))),
    )


def confirm_import_job(job_id: str) -> ImportConfirmResponse:
    jobs = load_import_jobs()
    payload = jobs.get(job_id)
    if payload is None:
        return ImportConfirmResponse(status="missing", jobId=job_id)

    preview = ImportPreview(**payload["preview"])
    if payload.get("confirmed"):
        return ImportConfirmResponse(
            status="already_confirmed",
            jobId=job_id,
            importType=preview.importType,
            rowCount=preview.rowCount,
            appliedCount=int(payload.get("appliedCount", 0)),
            affectedCollections=payload.get("affectedCollections", []),
            warnings=preview.warnings,
        )

    rows = payload.get("rows", [])
    import_records = load_import_records()
    import_records.setdefault(preview.importType, [])

    affected = [preview.importType]
    applied_count = len(rows)

    if preview.importType == "recurring_obligations":
        obligations = load_recurring_obligations()
        imported = [build_imported_obligation(row).model_dump() for row in rows]
        obligations.extend(imported)
        save_recurring_obligations(obligations)
        import_records["recurring_obligations"].extend(imported)
        affected.append("dashboard")
    else:
        import_records[preview.importType].extend(rows)

    import_records["history"].append(
        {
            "jobId": job_id,
            "importType": preview.importType,
            "filename": preview.filename,
            "rowCount": preview.rowCount,
            "appliedCount": applied_count,
            "confirmedAt": datetime.utcnow().isoformat() + "Z",
        }
    )
    save_import_records(import_records)

    payload["confirmed"] = True
    payload["appliedCount"] = applied_count
    payload["affectedCollections"] = affected
    jobs[job_id] = payload
    save_import_jobs(jobs)

    return ImportConfirmResponse(
        status="confirmed",
        jobId=job_id,
        importType=preview.importType,
        rowCount=preview.rowCount,
        appliedCount=applied_count,
        affectedCollections=affected,
        warnings=preview.warnings,
    )


def document_summary(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="ignore")[:280]
    if suffix == ".csv":
        reader = csv.reader(io.StringIO(content.decode("utf-8", errors="ignore")))
        header = next(reader, [])
        return f"Tabular document with columns: {', '.join(header)}"
    return "Document stored successfully. Rich extraction and OCR are deferred to the next milestone."


def store_document(kind: str, filename: str, content: bytes) -> BusinessDocument:
    documents = load_documents()
    document = BusinessDocument(
        id=f"doc-{uuid.uuid4().hex[:8]}",
        title=filename,
        kind=kind,
        summary=document_summary(filename, content),
        uploadedAt=date.today().isoformat(),
        stored=True,
    )
    documents.insert(0, document.model_dump())
    save_documents(documents)
    return document
