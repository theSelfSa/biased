from __future__ import annotations

import csv
import io
import json
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

import duckdb
import openpyxl
import polars as pl
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from api.config import get_settings
from api.models import (
    ActionCenterItem,
    ActionCenterSnapshot,
    ActionDraft,
    BriefingResult,
    BusinessDocument,
    CreateRecurringObligationRequest,
    ExpenseEntry,
    ImportCollectionSummary,
    ImportConfirmResponse,
    ImportHistoryEntry,
    ImportLedgerSnapshot,
    ImportPreview,
    InvestigationResult,
    PurchaseTransaction,
    QuickAddExpenseRequest,
    QuickAddPurchaseRequest,
    QuickAddSaleRequest,
    RecurringObligation,
    SalesTransaction,
)


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "data" / "demo").exists():
            return parent
    raise RuntimeError("Unable to locate repository root for demo data.")


DEMO_DIR = repo_root() / "data" / "demo"

REQUIRED_FIELDS: dict[str, set[str]] = {
    "sales": {"date", "sku", "amount_inr"},
    "purchases": {"date", "supplier_name", "sku", "amount_inr"},
    "products": {"sku", "name", "category", "quantity_on_hand"},
    "expenses": {"occurred_on", "label", "category", "amount_inr"},
    "recurring_obligations": {
        "label",
        "category",
        "amount_inr",
        "due_date",
        "recurrence",
    },
}

IMPORT_RECORD_TYPES = [
    "sales",
    "purchases",
    "products",
    "expenses",
    "recurring_obligations",
]


def load_json(name: str):
    return json.loads((DEMO_DIR / name).read_text(encoding="utf-8"))


@contextmanager
def db_cursor() -> Iterator[psycopg.Cursor]:
    settings = get_settings()
    connection = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ensure_operational_schema(cursor: psycopg.Cursor) -> None:
    cursor.execute("create extension if not exists pgcrypto")
    cursor.execute(
        """
        create table if not exists business_workspaces (
            id uuid primary key default gen_random_uuid(),
            name varchar(160) not null,
            slug varchar(160) not null unique,
            market varchar(64) not null default 'india',
            industry varchar(64) not null default 'pharmacy',
            base_currency varchar(8) not null default 'INR',
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists products (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            sku varchar(64) not null,
            name varchar(160) not null,
            category varchar(120) not null,
            unit_price_inr numeric(12,2) not null default 0,
            quantity_on_hand integer not null default 0,
            is_cold_chain boolean not null default false,
            expires_on text,
            created_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists sales_transactions (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            date text not null,
            sku varchar(64) not null,
            name varchar(160),
            category varchar(120),
            quantity integer not null default 0,
            amount_inr numeric(12,2) not null default 0,
            margin_pct numeric(6,2),
            created_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists purchase_transactions (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            date text not null,
            supplier_name varchar(160) not null,
            sku varchar(64) not null,
            quantity integer not null default 0,
            amount_inr numeric(12,2) not null default 0,
            created_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists expense_entries (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            label varchar(160) not null,
            category varchar(120) not null,
            amount_inr numeric(12,2) not null default 0,
            occurred_on text not null,
            created_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists recurring_obligations (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            label varchar(160) not null,
            category varchar(120) not null,
            amount_inr numeric(12,2) not null default 0,
            due_date text not null,
            recurrence varchar(32) not null,
            status varchar(32) not null default 'due',
            created_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists business_documents (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            title varchar(240) not null,
            kind varchar(64) not null,
            summary text not null,
            uploaded_at text not null,
            stored boolean not null default true,
            created_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists import_jobs (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            import_type varchar(64) not null,
            filename varchar(240) not null,
            row_count integer not null default 0,
            inferred_mappings jsonb not null default '{}'::jsonb,
            warnings jsonb not null default '[]'::jsonb,
            status varchar(32) not null default 'pending',
            applied_count integer not null default 0,
            affected_collections jsonb not null default '[]'::jsonb,
            created_at timestamptz not null default now(),
            confirmed_at timestamptz
        )
        """
    )
    cursor.execute(
        """
        create table if not exists import_job_rows (
            id uuid primary key,
            job_id uuid not null references import_jobs(id) on delete cascade,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            row_index integer not null,
            payload jsonb not null,
            created_at timestamptz not null default now()
        )
        """
    )


def ensure_workspace(cursor: psycopg.Cursor) -> dict[str, Any]:
    ensure_operational_schema(cursor)
    settings = get_settings()
    cursor.execute(
        """
        select id, name, slug
        from business_workspaces
        where slug = %s
        limit 1
        """,
        (settings.demo_workspace_slug,),
    )
    existing = cursor.fetchone()
    if existing is not None:
        return existing

    workspace_id = str(uuid.uuid4())
    cursor.execute(
        """
        insert into business_workspaces (id, name, slug, market, industry, base_currency)
        values (%s, %s, %s, 'india', 'pharmacy', 'INR')
        on conflict (slug) do nothing
        returning id, name, slug
        """,
        (workspace_id, settings.demo_workspace_name, settings.demo_workspace_slug),
    )
    workspace = cursor.fetchone()
    if workspace is None:
        cursor.execute(
            """
            select id, name, slug
            from business_workspaces
            where slug = %s
            limit 1
            """,
            (settings.demo_workspace_slug,),
        )
        workspace = cursor.fetchone()
    if workspace is None:
        raise RuntimeError("Unable to create or fetch the demo workspace.")
    return workspace


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


def sort_obligations(items: list[RecurringObligation]) -> list[RecurringObligation]:
    order = {"due": 0, "scheduled": 1, "paid": 2}
    return sorted(
        items,
        key=lambda item: (
            order.get(item.status, 1),
            item.dueDate,
            item.label,
        ),
    )


def to_float(value: Any, default: float = 0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return float(stripped)
        except ValueError:
            return default
    return default


def to_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, Decimal)):
        return int(value)
    if isinstance(value, float):
        return int(round(value))
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return int(float(stripped))
        except ValueError:
            return default
    return default


def normalize_sample_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def ensure_demo_seeded() -> None:
    with db_cursor() as cursor:
        workspace = ensure_workspace(cursor)
        workspace_id = workspace["id"]
        cursor.execute(
            "select count(*) as count from sales_transactions where workspace_id = %s",
            (workspace_id,),
        )
        sales_count = int(cursor.fetchone()["count"])
        if sales_count > 0:
            return

        seed_demo_workspace_data(reset=True, cursor=cursor, workspace_id=workspace_id)


def reset_demo_workspace_data() -> None:
    with db_cursor() as cursor:
        workspace = ensure_workspace(cursor)
        seed_demo_workspace_data(
            reset=True, cursor=cursor, workspace_id=workspace["id"]
        )


def seed_demo_workspace_data(
    reset: bool,
    cursor: psycopg.Cursor | None = None,
    workspace_id: str | None = None,
) -> None:
    if cursor is None:
        with db_cursor() as managed_cursor:
            workspace = ensure_workspace(managed_cursor)
            seed_demo_workspace_data(
                reset=reset,
                cursor=managed_cursor,
                workspace_id=workspace["id"],
            )
        return

    if workspace_id is None:
        workspace = ensure_workspace(cursor)
        workspace_id = workspace["id"]

    if reset:
        cursor.execute(
            "delete from import_job_rows where workspace_id = %s", (workspace_id,)
        )
        cursor.execute(
            "delete from import_jobs where workspace_id = %s", (workspace_id,)
        )
        cursor.execute(
            "delete from business_documents where workspace_id = %s", (workspace_id,)
        )
        cursor.execute(
            "delete from recurring_obligations where workspace_id = %s", (workspace_id,)
        )
        cursor.execute(
            "delete from expense_entries where workspace_id = %s", (workspace_id,)
        )
        cursor.execute(
            "delete from purchase_transactions where workspace_id = %s", (workspace_id,)
        )
        cursor.execute(
            "delete from sales_transactions where workspace_id = %s", (workspace_id,)
        )
        cursor.execute("delete from products where workspace_id = %s", (workspace_id,))

    products_path = DEMO_DIR / "pharmacy-products.csv"
    with products_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cursor.execute(
                """
                update products
                set
                    name = %s,
                    category = %s,
                    unit_price_inr = %s,
                    quantity_on_hand = %s,
                    expires_on = %s
                where workspace_id = %s and sku = %s
                returning id
                """,
                (
                    row["name"],
                    row["category"],
                    to_float(row["unit_price_inr"]),
                    to_int(row["quantity_on_hand"]),
                    row.get("expires_on") or None,
                    workspace_id,
                    row["sku"],
                ),
            )
            found = cursor.fetchone()
            if found is not None:
                continue
            cursor.execute(
                """
                insert into products (
                    id,
                    workspace_id,
                    sku,
                    name,
                    category,
                    unit_price_inr,
                    quantity_on_hand,
                    expires_on
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    workspace_id,
                    row["sku"],
                    row["name"],
                    row["category"],
                    to_float(row["unit_price_inr"]),
                    to_int(row["quantity_on_hand"]),
                    row.get("expires_on") or None,
                ),
            )

    sales_path = DEMO_DIR / "pharmacy-sales.csv"
    with sales_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cursor.execute(
                """
                select id
                from sales_transactions
                where workspace_id = %s and date = %s and sku = %s and amount_inr = %s
                limit 1
                """,
                (
                    workspace_id,
                    row["date"],
                    row["sku"],
                    to_float(row["revenue_inr"]),
                ),
            )
            if cursor.fetchone() is not None:
                continue
            cursor.execute(
                """
                insert into sales_transactions (
                    id,
                    workspace_id,
                    date,
                    sku,
                    name,
                    category,
                    quantity,
                    amount_inr,
                    margin_pct
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    workspace_id,
                    row["date"],
                    row["sku"],
                    row.get("product_name"),
                    row.get("category"),
                    to_int(row.get("qty"), 1),
                    to_float(row.get("revenue_inr")),
                    to_float(row.get("margin_pct"), 0),
                ),
            )

    purchases_path = DEMO_DIR / "pharmacy-purchases.csv"
    with purchases_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cursor.execute(
                """
                select id
                from purchase_transactions
                where workspace_id = %s and date = %s and sku = %s and amount_inr = %s
                limit 1
                """,
                (
                    workspace_id,
                    row["date"],
                    row["sku"],
                    to_float(row["amount_inr"]),
                ),
            )
            if cursor.fetchone() is not None:
                continue
            cursor.execute(
                """
                insert into purchase_transactions (
                    id,
                    workspace_id,
                    date,
                    supplier_name,
                    sku,
                    quantity,
                    amount_inr
                )
                values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    workspace_id,
                    row["date"],
                    row["supplier"],
                    row["sku"],
                    to_int(row["quantity"]),
                    to_float(row["amount_inr"]),
                ),
            )

    expenses_path = DEMO_DIR / "pharmacy-expenses.csv"
    with expenses_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cursor.execute(
                """
                select id
                from expense_entries
                where workspace_id = %s and occurred_on = %s and label = %s and amount_inr = %s
                limit 1
                """,
                (
                    workspace_id,
                    row["date"],
                    row["label"],
                    to_float(row["amount_inr"]),
                ),
            )
            if cursor.fetchone() is not None:
                continue
            cursor.execute(
                """
                insert into expense_entries (
                    id,
                    workspace_id,
                    label,
                    category,
                    amount_inr,
                    occurred_on
                )
                values (%s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    workspace_id,
                    row["label"],
                    row["category"],
                    to_float(row["amount_inr"]),
                    row["date"],
                ),
            )

    recurring_path = DEMO_DIR / "pharmacy-recurring-obligations.csv"
    with recurring_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cursor.execute(
                """
                select id
                from recurring_obligations
                where workspace_id = %s and label = %s and due_date = %s
                limit 1
                """,
                (
                    workspace_id,
                    row["label"],
                    row["due_date"],
                ),
            )
            if cursor.fetchone() is not None:
                continue
            cursor.execute(
                """
                insert into recurring_obligations (
                    id,
                    workspace_id,
                    label,
                    category,
                    amount_inr,
                    due_date,
                    recurrence,
                    status
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    workspace_id,
                    row["label"],
                    row["category"],
                    to_float(row["amount_inr"]),
                    row["due_date"],
                    normalize_recurrence(row["recurrence"]),
                    normalize_status(row.get("status")),
                ),
            )

    for document in load_json("pharmacy-documents.json"):
        cursor.execute(
            """
            select id
            from business_documents
            where workspace_id = %s and title = %s and uploaded_at = %s
            limit 1
            """,
            (workspace_id, document["title"], document["uploadedAt"]),
        )
        if cursor.fetchone() is not None:
            continue
        cursor.execute(
            """
            insert into business_documents (
                id,
                workspace_id,
                title,
                kind,
                summary,
                uploaded_at,
                stored
            )
            values (%s, %s, %s, %s, %s, %s, true)
            """,
            (
                str(uuid.uuid4()),
                workspace_id,
                document["title"],
                document["kind"],
                document["summary"],
                document["uploadedAt"],
            ),
        )


def map_recurring_row(row: dict[str, Any]) -> RecurringObligation:
    return RecurringObligation(
        id=str(row["id"]),
        label=str(row["label"]),
        category=str(row["category"]),
        amountInr=to_float(row.get("amount_inr")),
        dueDate=str(row["due_date"]),
        recurrence=normalize_recurrence(str(row.get("recurrence"))),
        status=normalize_status(str(row.get("status"))),
    )


def load_recurring_obligations() -> list[RecurringObligation]:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            select id, label, category, amount_inr, due_date, recurrence, status
            from recurring_obligations
            where workspace_id = %s
            """,
            (workspace_id,),
        )
        obligations = [map_recurring_row(row) for row in cursor.fetchall()]
    return sort_obligations(obligations)


def create_recurring_obligation(
    payload: CreateRecurringObligationRequest,
) -> RecurringObligation:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        obligation_id = str(uuid.uuid4())
        cursor.execute(
            """
            insert into recurring_obligations (
                id,
                workspace_id,
                label,
                category,
                amount_inr,
                due_date,
                recurrence,
                status
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            returning id, label, category, amount_inr, due_date, recurrence, status
            """,
            (
                obligation_id,
                workspace_id,
                payload.label.strip(),
                payload.category.strip(),
                round(float(payload.amountInr), 2),
                payload.dueDate,
                normalize_recurrence(payload.recurrence),
                normalize_status(payload.status),
            ),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Unable to save recurring obligation.")
    return map_recurring_row(row)


def mark_recurring_obligation_status(
    obligation_id: str, status: str
) -> RecurringObligation | None:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            update recurring_obligations
            set status = %s
            where id = %s and workspace_id = %s
            returning id, label, category, amount_inr, due_date, recurrence, status
            """,
            (normalize_status(status), obligation_id, workspace_id),
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return map_recurring_row(row)


def map_document_row(row: dict[str, Any]) -> BusinessDocument:
    return BusinessDocument(
        id=str(row["id"]),
        title=str(row["title"]),
        kind=str(row["kind"]),
        summary=str(row["summary"]),
        uploadedAt=str(row["uploaded_at"]),
        stored=bool(row.get("stored", True)),
    )


def load_documents() -> list[BusinessDocument]:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            select id, title, kind, summary, uploaded_at, stored
            from business_documents
            where workspace_id = %s
            order by uploaded_at desc, created_at desc
            """,
            (workspace_id,),
        )
        return [map_document_row(row) for row in cursor.fetchall()]


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
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        document_id = str(uuid.uuid4())
        summary = document_summary(filename, content)
        uploaded_at = date.today().isoformat()
        cursor.execute(
            """
            insert into business_documents (
                id,
                workspace_id,
                title,
                kind,
                summary,
                uploaded_at,
                stored
            )
            values (%s, %s, %s, %s, %s, %s, true)
            returning id, title, kind, summary, uploaded_at, stored
            """,
            (
                document_id,
                workspace_id,
                filename,
                kind,
                summary,
                uploaded_at,
            ),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Unable to store document.")
    return map_document_row(row)


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
        if not rows:
            return pl.DataFrame([])
        headers = [str(value) for value in rows[0]]
        records = [dict(zip(headers, row, strict=False)) for row in rows[1:]]
        return pl.DataFrame(records)

    raise ValueError(
        "Only CSV and Excel files are supported in the current preview flow."
    )


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
    normalized = {
        column: column.strip().lower().replace(" ", "_") for column in columns
    }
    mapping = aliases.get(import_type, {})
    return {
        source: mapping.get(alias, "review_manually")
        for source, alias in normalized.items()
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
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "item"):
        return value.item()
    return value


def normalize_rows(
    frame: pl.DataFrame, inferred: dict[str, str]
) -> list[dict[str, Any]]:
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


def preview_upload(
    import_type: str, filename: str, content: bytes
) -> tuple[ImportPreview, list[dict[str, Any]]]:
    frame = read_tabular_upload(filename, content)
    inferred = infer_mappings(import_type, [str(column) for column in frame.columns])

    warnings: list[str] = []
    manual_review = [
        source for source, target in inferred.items() if target == "review_manually"
    ]
    if manual_review:
        warnings.append(
            "Some columns need manual review: " + ", ".join(sorted(manual_review))
        )

    required_fields = REQUIRED_FIELDS.get(import_type, set())
    missing_fields = sorted(required_fields.difference(inferred.values()))
    if missing_fields:
        warnings.append("Missing canonical mappings: " + ", ".join(missing_fields))

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


def store_import_job(preview: ImportPreview, rows: list[dict[str, Any]]) -> str:
    ensure_demo_seeded()
    job_id = str(uuid.uuid4())
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            insert into import_jobs (
                id,
                workspace_id,
                import_type,
                filename,
                row_count,
                inferred_mappings,
                warnings,
                status
            )
            values (%s, %s, %s, %s, %s, %s, %s, 'pending')
            """,
            (
                job_id,
                workspace_id,
                preview.importType,
                preview.filename,
                int(preview.rowCount),
                Json(preview.inferredMappings),
                Json(preview.warnings),
            ),
        )
        for row_index, row in enumerate(rows):
            cursor.execute(
                """
                insert into import_job_rows (id, job_id, workspace_id, row_index, payload)
                values (%s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    job_id,
                    workspace_id,
                    row_index,
                    Json(row),
                ),
            )
    return job_id


def apply_sale_row(
    cursor: psycopg.Cursor, workspace_id: str, row: dict[str, Any]
) -> None:
    cursor.execute(
        """
        insert into sales_transactions (
            id,
            workspace_id,
            date,
            sku,
            name,
            category,
            quantity,
            amount_inr,
            margin_pct
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            workspace_id,
            str(row.get("date", date.today().isoformat())),
            str(row.get("sku", "UNKNOWN")),
            (str(row["name"]) if row.get("name") is not None else None),
            (str(row["category"]) if row.get("category") is not None else None),
            to_int(row.get("quantity"), 1),
            round(to_float(row.get("amount_inr")), 2),
            (
                round(to_float(row.get("margin_pct")), 2)
                if row.get("margin_pct") is not None
                else None
            ),
        ),
    )


def apply_purchase_row(
    cursor: psycopg.Cursor, workspace_id: str, row: dict[str, Any]
) -> None:
    cursor.execute(
        """
        insert into purchase_transactions (
            id,
            workspace_id,
            date,
            supplier_name,
            sku,
            quantity,
            amount_inr
        )
        values (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            workspace_id,
            str(row.get("date", date.today().isoformat())),
            str(row.get("supplier_name", "Unknown supplier")),
            str(row.get("sku", "UNKNOWN")),
            to_int(row.get("quantity"), 1),
            round(to_float(row.get("amount_inr")), 2),
        ),
    )


def apply_product_row(
    cursor: psycopg.Cursor, workspace_id: str, row: dict[str, Any]
) -> None:
    sku = str(row.get("sku", "")).strip()
    if not sku:
        return
    cursor.execute(
        """
        update products
        set
            name = %s,
            category = %s,
            unit_price_inr = %s,
            quantity_on_hand = %s,
            expires_on = %s
        where workspace_id = %s and sku = %s
        returning id
        """,
        (
            str(row.get("name", sku)),
            str(row.get("category", "General")),
            round(to_float(row.get("unit_price_inr")), 2),
            to_int(row.get("quantity_on_hand"), 0),
            (str(row["expires_on"]) if row.get("expires_on") else None),
            workspace_id,
            sku,
        ),
    )
    if cursor.fetchone() is not None:
        return
    cursor.execute(
        """
        insert into products (
            id,
            workspace_id,
            sku,
            name,
            category,
            unit_price_inr,
            quantity_on_hand,
            expires_on
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            workspace_id,
            sku,
            str(row.get("name", sku)),
            str(row.get("category", "General")),
            round(to_float(row.get("unit_price_inr")), 2),
            to_int(row.get("quantity_on_hand"), 0),
            (str(row["expires_on"]) if row.get("expires_on") else None),
        ),
    )


def apply_expense_row(
    cursor: psycopg.Cursor, workspace_id: str, row: dict[str, Any]
) -> None:
    cursor.execute(
        """
        insert into expense_entries (
            id,
            workspace_id,
            label,
            category,
            amount_inr,
            occurred_on
        )
        values (%s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            workspace_id,
            str(row.get("label", "Expense entry")),
            str(row.get("category", "Operations")),
            round(to_float(row.get("amount_inr")), 2),
            str(row.get("occurred_on", date.today().isoformat())),
        ),
    )


def apply_recurring_row(
    cursor: psycopg.Cursor, workspace_id: str, row: dict[str, Any]
) -> None:
    cursor.execute(
        """
        insert into recurring_obligations (
            id,
            workspace_id,
            label,
            category,
            amount_inr,
            due_date,
            recurrence,
            status
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            workspace_id,
            str(row.get("label", "Imported obligation")),
            str(row.get("category", "Operations")),
            round(to_float(row.get("amount_inr")), 2),
            str(row.get("due_date", date.today().isoformat())),
            normalize_recurrence(str(row.get("recurrence", "monthly"))),
            normalize_status(str(row.get("status", "scheduled"))),
        ),
    )


def confirm_import_job(job_id: str) -> ImportConfirmResponse:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            select
                id,
                import_type,
                filename,
                row_count,
                inferred_mappings,
                warnings,
                status,
                applied_count,
                affected_collections
            from import_jobs
            where id = %s and workspace_id = %s
            limit 1
            """,
            (job_id, workspace_id),
        )
        job = cursor.fetchone()
        if job is None:
            return ImportConfirmResponse(status="missing", jobId=job_id)

        warnings = [str(item) for item in (job.get("warnings") or [])]
        affected_collections = [
            str(item) for item in (job.get("affected_collections") or [])
        ]
        if job["status"] == "confirmed":
            return ImportConfirmResponse(
                status="already_confirmed",
                jobId=job_id,
                importType=str(job["import_type"]),
                rowCount=int(job["row_count"] or 0),
                appliedCount=int(job.get("applied_count") or 0),
                affectedCollections=affected_collections,
                warnings=warnings,
            )

        cursor.execute(
            """
            select payload
            from import_job_rows
            where job_id = %s and workspace_id = %s
            order by row_index asc
            """,
            (job_id, workspace_id),
        )
        rows = [dict(row["payload"]) for row in cursor.fetchall()]

        import_type = str(job["import_type"])
        for row in rows:
            if import_type == "sales":
                apply_sale_row(cursor, workspace_id, row)
                continue
            if import_type == "purchases":
                apply_purchase_row(cursor, workspace_id, row)
                continue
            if import_type == "products":
                apply_product_row(cursor, workspace_id, row)
                continue
            if import_type == "expenses":
                apply_expense_row(cursor, workspace_id, row)
                continue
            if import_type == "recurring_obligations":
                apply_recurring_row(cursor, workspace_id, row)

        applied_count = len(rows)
        affected = [import_type]
        if import_type in {
            "sales",
            "purchases",
            "expenses",
            "products",
            "recurring_obligations",
        }:
            affected.append("dashboard")
        if import_type in {"sales", "purchases", "expenses"}:
            affected.append("action_queue")

        cursor.execute(
            """
            update import_jobs
            set
                status = 'confirmed',
                applied_count = %s,
                affected_collections = %s,
                confirmed_at = now()
            where id = %s and workspace_id = %s
            """,
            (
                applied_count,
                Json(affected),
                job_id,
                workspace_id,
            ),
        )

        return ImportConfirmResponse(
            status="confirmed",
            jobId=job_id,
            importType=import_type,
            rowCount=int(job["row_count"] or 0),
            appliedCount=applied_count,
            affectedCollections=affected,
            warnings=warnings,
        )


def latest_history_for_type(
    history: list[dict[str, Any]], import_type: str
) -> str | None:
    for item in history:
        if item["importType"] == import_type:
            return str(item["confirmedAt"])
    return None


def collection_rows(
    cursor: psycopg.Cursor, workspace_id: str, import_type: str
) -> tuple[int, list[str], list[dict[str, Any]]]:
    if import_type == "sales":
        cursor.execute(
            """
            select date, sku, name, category, quantity, amount_inr, margin_pct
            from sales_transactions
            where workspace_id = %s
            order by date desc, created_at desc
            limit 3
            """,
            (workspace_id,),
        )
        sample_rows = [
            {key: normalize_sample_value(value) for key, value in row.items()}
            for row in cursor.fetchall()
        ]
        cursor.execute(
            "select count(*) as count from sales_transactions where workspace_id = %s",
            (workspace_id,),
        )
        row_count = int(cursor.fetchone()["count"])
        columns = [
            "date",
            "sku",
            "name",
            "category",
            "quantity",
            "amount_inr",
            "margin_pct",
        ]
        return row_count, columns, list(reversed(sample_rows))

    if import_type == "purchases":
        cursor.execute(
            """
            select date, supplier_name, sku, quantity, amount_inr
            from purchase_transactions
            where workspace_id = %s
            order by date desc, created_at desc
            limit 3
            """,
            (workspace_id,),
        )
        sample_rows = [
            {key: normalize_sample_value(value) for key, value in row.items()}
            for row in cursor.fetchall()
        ]
        cursor.execute(
            "select count(*) as count from purchase_transactions where workspace_id = %s",
            (workspace_id,),
        )
        row_count = int(cursor.fetchone()["count"])
        columns = ["date", "supplier_name", "sku", "quantity", "amount_inr"]
        return row_count, columns, list(reversed(sample_rows))

    if import_type == "products":
        cursor.execute(
            """
            select sku, name, category, unit_price_inr, quantity_on_hand, expires_on
            from products
            where workspace_id = %s
            order by created_at desc
            limit 3
            """,
            (workspace_id,),
        )
        sample_rows = [
            {key: normalize_sample_value(value) for key, value in row.items()}
            for row in cursor.fetchall()
        ]
        cursor.execute(
            "select count(*) as count from products where workspace_id = %s",
            (workspace_id,),
        )
        row_count = int(cursor.fetchone()["count"])
        columns = [
            "sku",
            "name",
            "category",
            "unit_price_inr",
            "quantity_on_hand",
            "expires_on",
        ]
        return row_count, columns, list(reversed(sample_rows))

    if import_type == "expenses":
        cursor.execute(
            """
            select occurred_on, label, category, amount_inr
            from expense_entries
            where workspace_id = %s
            order by occurred_on desc, created_at desc
            limit 3
            """,
            (workspace_id,),
        )
        sample_rows = [
            {key: normalize_sample_value(value) for key, value in row.items()}
            for row in cursor.fetchall()
        ]
        cursor.execute(
            "select count(*) as count from expense_entries where workspace_id = %s",
            (workspace_id,),
        )
        row_count = int(cursor.fetchone()["count"])
        columns = ["occurred_on", "label", "category", "amount_inr"]
        return row_count, columns, list(reversed(sample_rows))

    cursor.execute(
        """
        select label, category, amount_inr, due_date, recurrence, status
        from recurring_obligations
        where workspace_id = %s
        order by due_date desc, created_at desc
        limit 3
        """,
        (workspace_id,),
    )
    sample_rows = [
        {key: normalize_sample_value(value) for key, value in row.items()}
        for row in cursor.fetchall()
    ]
    cursor.execute(
        "select count(*) as count from recurring_obligations where workspace_id = %s",
        (workspace_id,),
    )
    row_count = int(cursor.fetchone()["count"])
    columns = ["label", "category", "amount_inr", "due_date", "recurrence", "status"]
    return row_count, columns, list(reversed(sample_rows))


def build_import_ledger() -> ImportLedgerSnapshot:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]

        cursor.execute(
            """
            select
                id,
                import_type,
                filename,
                row_count,
                applied_count,
                confirmed_at
            from import_jobs
            where workspace_id = %s and status = 'confirmed'
            order by confirmed_at desc nulls last, created_at desc
            """,
            (workspace_id,),
        )
        history_rows = cursor.fetchall()
        history = [
            ImportHistoryEntry(
                jobId=str(row["id"]),
                importType=str(row["import_type"]),
                filename=str(row["filename"]),
                rowCount=int(row["row_count"] or 0),
                appliedCount=int(row["applied_count"] or 0),
                confirmedAt=(
                    row["confirmed_at"].isoformat() if row.get("confirmed_at") else ""
                ),
            ).model_dump()
            for row in history_rows
        ]

        collections: list[ImportCollectionSummary] = []
        for import_type in IMPORT_RECORD_TYPES:
            row_count, columns, sample_rows = collection_rows(
                cursor, workspace_id, import_type
            )
            collections.append(
                ImportCollectionSummary(
                    importType=import_type,
                    rowCount=row_count,
                    latestImportAt=latest_history_for_type(history, import_type),
                    columns=columns,
                    sampleRows=sample_rows,
                )
            )

    return ImportLedgerSnapshot(
        history=[ImportHistoryEntry(**item) for item in history],
        collections=collections,
    )


def map_sale_row(row: dict[str, Any]) -> SalesTransaction:
    return SalesTransaction(
        id=str(row["id"]),
        date=str(row["date"]),
        sku=str(row["sku"]),
        name=(str(row["name"]) if row.get("name") is not None else None),
        category=(str(row["category"]) if row.get("category") is not None else None),
        quantity=to_int(row.get("quantity")),
        amountInr=to_float(row.get("amount_inr")),
        marginPct=(
            round(to_float(row.get("margin_pct")), 2)
            if row.get("margin_pct") is not None
            else None
        ),
    )


def map_purchase_row(row: dict[str, Any]) -> PurchaseTransaction:
    return PurchaseTransaction(
        id=str(row["id"]),
        date=str(row["date"]),
        supplierName=str(row["supplier_name"]),
        sku=str(row["sku"]),
        quantity=to_int(row.get("quantity")),
        amountInr=to_float(row.get("amount_inr")),
    )


def map_expense_row(row: dict[str, Any]) -> ExpenseEntry:
    return ExpenseEntry(
        id=str(row["id"]),
        occurredOn=str(row["occurred_on"]),
        label=str(row["label"]),
        category=str(row["category"]),
        amountInr=to_float(row.get("amount_inr")),
    )


def quick_add_sale(payload: QuickAddSaleRequest) -> SalesTransaction:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            insert into sales_transactions (
                id,
                workspace_id,
                date,
                sku,
                name,
                category,
                quantity,
                amount_inr,
                margin_pct
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            returning id, date, sku, name, category, quantity, amount_inr, margin_pct
            """,
            (
                str(uuid.uuid4()),
                workspace_id,
                payload.date,
                payload.sku,
                payload.name,
                payload.category,
                payload.quantity,
                round(float(payload.amountInr), 2),
                (
                    round(float(payload.marginPct), 2)
                    if payload.marginPct is not None
                    else None
                ),
            ),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Unable to save sales entry.")
    return map_sale_row(row)


def quick_add_purchase(payload: QuickAddPurchaseRequest) -> PurchaseTransaction:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            insert into purchase_transactions (
                id,
                workspace_id,
                date,
                supplier_name,
                sku,
                quantity,
                amount_inr
            )
            values (%s, %s, %s, %s, %s, %s, %s)
            returning id, date, supplier_name, sku, quantity, amount_inr
            """,
            (
                str(uuid.uuid4()),
                workspace_id,
                payload.date,
                payload.supplierName,
                payload.sku,
                payload.quantity,
                round(float(payload.amountInr), 2),
            ),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Unable to save purchase entry.")
    return map_purchase_row(row)


def quick_add_expense(payload: QuickAddExpenseRequest) -> ExpenseEntry:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            insert into expense_entries (
                id,
                workspace_id,
                label,
                category,
                amount_inr,
                occurred_on
            )
            values (%s, %s, %s, %s, %s, %s)
            returning id, occurred_on, label, category, amount_inr
            """,
            (
                str(uuid.uuid4()),
                workspace_id,
                payload.label,
                payload.category,
                round(float(payload.amountInr), 2),
                payload.occurredOn,
            ),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Unable to save expense entry.")
    return map_expense_row(row)


def due_days(item: RecurringObligation) -> int:
    return (parse_iso_date(item.dueDate) - date.today()).days


def format_action_amount(amount: float) -> str:
    return f"₹{amount:,.0f}"


def build_action_queue() -> ActionCenterSnapshot:
    obligations = load_recurring_obligations()
    import_ledger = build_import_ledger()
    queue: list[ActionCenterItem] = []

    unpaid = [item for item in obligations if item.status != "paid"]
    due_soon = sorted(unpaid, key=due_days)

    for item in due_soon[:3]:
        days = due_days(item)
        is_supplier = item.category.lower() == "supplier"
        if is_supplier:
            queue.append(
                ActionCenterItem(
                    id=f"draft-{item.id}",
                    title=f"Stage supplier follow-up for {item.label}",
                    detail=(
                        f"{format_action_amount(item.amountInr)} is due on {item.dueDate}. "
                        "Prepare a message before the next payment cycle tightens cash."
                    ),
                    severity="critical" if days <= 3 else "warning",
                    actionType="vendor_follow_up",
                    targetEntity=item.label,
                    status="open",
                )
            )
            continue

        queue.append(
            ActionCenterItem(
                id=f"obligation-{item.id}",
                title=f"Protect cash for {item.label}",
                detail=(
                    f"{format_action_amount(item.amountInr)} is "
                    f"{('overdue' if days < 0 else f'due in {days} days')} and should stay visible in the owner plan."
                ),
                severity="critical" if days <= 2 else "warning",
                actionType="bill_review",
                targetEntity=item.label,
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
        queue = [
            ActionCenterItem(
                id="watch-stock",
                title="No urgent actions. Keep tracking slow-moving stock.",
                detail="Your current obligations look stable. Use quick-add entries to keep decisions up to date.",
                severity="info",
                actionType="watchlist",
                targetEntity="Current workspace",
                status="watching",
            )
        ]

    headline = (
        "Focus first on obligations that can tighten cash, then use the imported ledgers "
        "to validate what changed most recently."
    )
    return ActionCenterSnapshot(headline=headline, items=queue)


def load_dashboard() -> dict[str, Any]:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace = ensure_workspace(cursor)
        workspace_id = workspace["id"]

        cursor.execute(
            """
            select
                to_char(to_date(date, 'YYYY-MM-DD'), 'Mon') as month_label,
                sum(amount_inr)::float as revenue_inr,
                avg(margin_pct)::float as margin_pct
            from sales_transactions
            where workspace_id = %s
            group by month_label, to_char(to_date(date, 'YYYY-MM-DD'), 'MM')
            order by to_char(to_date(date, 'YYYY-MM-DD'), 'MM')
            """,
            (workspace_id,),
        )
        margin_series = [
            {
                "label": str(row["month_label"]),
                "revenueInr": round(to_float(row["revenue_inr"]), 2),
                "marginPct": round(to_float(row["margin_pct"]), 2),
            }
            for row in cursor.fetchall()
        ]

        cursor.execute(
            """
            select
                coalesce(sum(amount_inr), 0)::float as total_revenue,
                coalesce(avg(margin_pct), 0)::float as avg_margin
            from sales_transactions
            where workspace_id = %s
            """,
            (workspace_id,),
        )
        sales_stats = cursor.fetchone() or {"total_revenue": 0.0, "avg_margin": 0.0}
        total_revenue = to_float(sales_stats.get("total_revenue"))
        avg_margin = to_float(sales_stats.get("avg_margin"))

        cursor.execute(
            """
            select id, label, category, amount_inr, due_date, recurrence, status
            from recurring_obligations
            where workspace_id = %s
            """,
            (workspace_id,),
        )
        obligations = sort_obligations(
            [map_recurring_row(row) for row in cursor.fetchall()]
        )
        due_soon = [
            item
            for item in obligations
            if item.status != "paid" and 0 <= due_days(item) <= 10
        ]
        total_due_soon = sum(item.amountInr for item in due_soon)
        due_labels = (
            ", ".join(item.label for item in due_soon[:3])
            or "No recurring bills due soon"
        )

        horizon = (date.today() + timedelta(days=45)).isoformat()
        cursor.execute(
            """
            select
                count(*)::int as lot_count,
                coalesce(sum(unit_price_inr * quantity_on_hand), 0)::float as exposure
            from products
            where workspace_id = %s and expires_on is not null and expires_on <= %s
            """,
            (workspace_id, horizon),
        )
        expiry = cursor.fetchone() or {"lot_count": 0, "exposure": 0.0}
        near_expiry_count = int(expiry.get("lot_count") or 0)
        near_expiry_exposure = to_float(expiry.get("exposure"))

        cursor.execute(
            """
            select
                p.sku,
                p.name,
                p.expires_on,
                p.quantity_on_hand
            from products p
            where p.workspace_id = %s and p.expires_on is not null and p.expires_on <= %s
            order by p.expires_on asc
            limit 2
            """,
            (workspace_id, horizon),
        )
        risky_products = cursor.fetchall()

    inventory_alerts: list[dict[str, Any]] = []
    if risky_products:
        product = risky_products[0]
        inventory_alerts.append(
            {
                "id": f"expiry-{product['sku']}",
                "title": f"{product['name']} needs expiry attention",
                "detail": (
                    f"SKU {product['sku']} expires on {product['expires_on']} with "
                    f"{to_int(product['quantity_on_hand'])} units on hand."
                ),
                "severity": "warning",
            }
        )

    inventory_alerts.append(
        {
            "id": "cash-watch",
            "title": "Recurring obligations are now DB-backed and live",
            "detail": "Use quick-add entries to keep daily sales, purchases, and expenses decision-ready.",
            "severity": "info",
        }
    )

    action_center = build_action_queue()

    return {
        "workspaceName": workspace["name"],
        "subtitle": "Owner command center for margin, stock, and recurring obligations.",
        "stats": [
            {
                "label": "Monthly revenue",
                "value": format_inr_short(total_revenue),
                "delta": "Computed from imported and quick-added sales rows",
                "tone": "positive" if total_revenue > 0 else "neutral",
            },
            {
                "label": "Gross margin",
                "value": f"{avg_margin:.1f}%",
                "delta": "Average of tracked sale-level margin entries",
                "tone": "warning" if avg_margin < 24 else "positive",
            },
            {
                "label": "Bills due in 10 days",
                "value": format_inr_short(total_due_soon),
                "delta": due_labels,
                "tone": "critical" if total_due_soon else "neutral",
            },
            {
                "label": "Near-expiry inventory",
                "value": format_inr_short(near_expiry_exposure),
                "delta": f"{near_expiry_count} lots inside 45-day watch window",
                "tone": "warning" if near_expiry_count else "neutral",
            },
        ],
        "marginSeries": margin_series,
        "obligations": [item.model_dump() for item in obligations],
        "inventoryAlerts": inventory_alerts,
        "actionQueue": [item.model_dump() for item in action_center.items[:4]],
    }


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
    dashboard = load_dashboard()
    obligations = load_recurring_obligations()
    due_today = [
        f"{item.label} — ₹{item.amountInr:,.0f}"
        for item in obligations
        if item.status != "paid" and item.dueDate <= date.today().isoformat()
    ]

    action_queue = build_action_queue()
    anomalies = [
        alert["title"]
        for alert in dashboard["inventoryAlerts"]
        if alert["severity"] in {"critical", "warning"}
    ]
    suggested = [item.title for item in action_queue.items[:2]]
    return BriefingResult(
        headline="Daily owner brief generated from Postgres-backed business memory.",
        items=[
            f"Revenue snapshot: {dashboard['stats'][0]['value']}",
            f"Gross margin snapshot: {dashboard['stats'][1]['value']}",
            f"Bills due soon: {dashboard['stats'][2]['value']}",
        ],
        dueToday=due_today or ["No recurring payments due today."],
        anomalies=anomalies or ["No major anomalies detected in the current snapshot."],
        suggestedActions=suggested
        or [
            "Add today's sales, purchases, and expenses to tighten tomorrow's recommendations."
        ],
    )


def generate_investigation(question: str) -> InvestigationResult:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        cursor.execute(
            """
            select coalesce(avg(amount_inr), 0)::float as utility_avg
            from expense_entries
            where workspace_id = %s and lower(category) = 'utilities'
            """,
            (workspace_id,),
        )
        utility_avg = to_float((cursor.fetchone() or {}).get("utility_avg"))

        cursor.execute(
            """
            select coalesce(max(amount_inr), 0)::float as top_supplier_due
            from recurring_obligations
            where workspace_id = %s and lower(category) = 'supplier' and status <> 'paid'
            """,
            (workspace_id,),
        )
        upcoming_supplier = to_float((cursor.fetchone() or {}).get("top_supplier_due"))

        horizon = (date.today() + timedelta(days=45)).isoformat()
        cursor.execute(
            """
            select count(*)::int as near_expiry_count
            from products
            where workspace_id = %s and expires_on is not null and expires_on <= %s
            """,
            (workspace_id, horizon),
        )
        near_expiry = int((cursor.fetchone() or {}).get("near_expiry_count") or 0)

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
        item = next(
            (entry for entry in action_queue if entry.actionType == "vendor_follow_up"),
            None,
        )

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
