from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date
from pathlib import Path

import duckdb
import openpyxl
import polars as pl

from api.models import ActionDraft, BriefingResult, ImportPreview, InvestigationResult


IMPORT_JOBS: dict[str, ImportPreview] = {}


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "data" / "demo").exists():
            return parent
    raise RuntimeError("Unable to locate repository root for demo data.")


DEMO_DIR = repo_root() / "data" / "demo"


def load_json(name: str):
    return json.loads((DEMO_DIR / name).read_text(encoding="utf-8"))


def load_dashboard():
    return load_json("pharmacy-dashboard.json")


def load_documents():
    return load_json("pharmacy-documents.json")


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
    return BriefingResult(**load_json("pharmacy-briefing.json"))


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
    return ActionDraft(
        actionType="vendor_follow_up",
        targetEntity=f"action:{action_id}",
        rationale="Short-term cash preservation is better than carrying more slow inventory.",
        draftText=(
            "Hello, we would like to stagger the next settlement and trim the dermatology "
            "reorder size for this cycle while we move the current inventory first."
        ),
        approvalRequired=True,
    )


def preview_upload(import_type: str, filename: str, content: bytes) -> ImportPreview:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        frame = pl.read_csv(io.BytesIO(content))
    elif suffix in {".xlsx", ".xlsm"}:
        workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        sheet = workbook.active
        rows = list(sheet.values)
        headers = [str(value) for value in rows[0]]
        records = [dict(zip(headers, row, strict=False)) for row in rows[1:]]
        frame = pl.DataFrame(records)
    else:
        raise ValueError("Only CSV and Excel files are supported in the current preview flow.")

    inferred = infer_mappings(import_type, list(frame.columns))
    warnings: list[str] = []
    if "date" not in {value.lower() for value in frame.columns}:
        warnings.append("No canonical date column was detected. Review your mapping before import.")

    return ImportPreview(
        importType=import_type,
        filename=filename,
        rowCount=frame.height,
        columns=list(frame.columns),
        inferredMappings=inferred,
        warnings=warnings,
    )


def infer_mappings(import_type: str, columns: list[str]) -> dict[str, str]:
    aliases = {
        "sales": {
            "date": "date",
            "sku": "sku",
            "product_name": "name",
            "qty": "quantity",
            "revenue_inr": "amount_inr",
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
        },
    }
    normalized = {column: column.strip().lower().replace(" ", "_") for column in columns}
    mapping = aliases.get(import_type, {})
    return {
        source: mapping.get(alias, "review_manually")
        for source, alias in normalized.items()
    }


def store_import_job(preview: ImportPreview) -> str:
    job_id = str(uuid.uuid4())
    IMPORT_JOBS[job_id] = preview
    return job_id


def confirm_import_job(job_id: str):
    preview = IMPORT_JOBS.get(job_id)
    if preview is None:
        return {"status": "missing", "jobId": job_id}

    return {
        "status": "confirmed",
        "jobId": job_id,
        "importType": preview.importType,
        "rowCount": preview.rowCount,
    }


def document_summary(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="ignore")[:280]
    if suffix == ".csv":
        reader = csv.reader(io.StringIO(content.decode("utf-8", errors="ignore")))
        header = next(reader, [])
        return f"Tabular document with columns: {', '.join(header)}"
    return "Document stored successfully. Rich extraction and OCR are deferred to the next milestone."
