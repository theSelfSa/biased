from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import time
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
    ActionStatusUpdateRequest,
    ActionStatusUpdateResponse,
    BriefingResult,
    BusinessDocument,
    CreateRecurringObligationRequest,
    ExpenseEntry,
    ForecastResult,
    ImportCollectionSummary,
    ImportConfirmResponse,
    ImportHistoryEntry,
    ImportLedgerSnapshot,
    ImportPreview,
    InvestigationResult,
    ModelProfile,
    ModelProviderSettings,
    ModelProviderSettingsResponse,
    PurchaseTransaction,
    QuickAddExpenseRequest,
    QuickAddPurchaseRequest,
    QuickAddSaleRequest,
    RecurringObligation,
    ScenarioDelta,
    ScenarioPlannerRequest,
    ScenarioPlannerResult,
    SchedulerRunResult,
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
    cursor.execute("create extension if not exists vector")
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
    cursor.execute(
        """
        create table if not exists model_provider_settings (
            workspace_id uuid primary key references business_workspaces(id) on delete cascade,
            mode varchar(32) not null default 'local-open',
            providers jsonb not null default '[]'::jsonb,
            updated_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists document_chunks (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            document_id uuid not null references business_documents(id) on delete cascade,
            chunk_index integer not null,
            content text not null,
            embedding vector(24) not null,
            created_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists action_center_items (
            id varchar(120) primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            title varchar(240) not null,
            detail text not null,
            severity varchar(32) not null,
            action_type varchar(64) not null,
            target_entity varchar(200) not null,
            status varchar(32) not null default 'open',
            snoozed_until text,
            resolution_note text,
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        )
        """
    )
    cursor.execute(
        """
        create table if not exists scheduler_runs (
            id uuid primary key,
            workspace_id uuid not null references business_workspaces(id) on delete cascade,
            morning_brief_id varchar(120) not null,
            anomaly_count integer not null default 0,
            due_reminder_count integer not null default 0,
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


def normalize_model_mode(value: str | None) -> str:
    if value in {"local-open", "byo-cloud", "hybrid"}:
        return value
    return "local-open"


def normalize_provider_list(providers: list[str] | None) -> list[str]:
    if not providers:
        return []
    deduped: list[str] = []
    seen: set[str] = set()
    for provider in providers:
        current = provider.strip().lower()
        if not current or current in seen:
            continue
        seen.add(current)
        deduped.append(current)
    return deduped


def chunk_text(content: str, size: int = 280) -> list[str]:
    cleaned = " ".join(content.split())
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += size
    return chunks


def embedding_for_text(content: str, dim: int = 24) -> list[float]:
    vector = [0.0] * dim
    tokens = content.lower().split()
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        slot = int(digest[:8], 16) % dim
        sign = -1.0 if int(digest[8:10], 16) % 2 else 1.0
        weight = (int(digest[10:14], 16) % 1000) / 1000.0
        vector[slot] += sign * (0.25 + weight)
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in vector) + "]"


def guard_question(question: str) -> str | None:
    lowered = question.lower()
    blocked_patterns = [
        "drop ",
        "delete ",
        "truncate ",
        "alter ",
        "grant ",
        "revoke ",
        ";",
        "--",
    ]
    if any(pattern in lowered for pattern in blocked_patterns):
        return (
            "This request looks like a direct SQL control statement. "
            "B.I.A.S.E.D. only supports safe, read-only business analytics prompts."
        )
    return None


def infer_task_class(question: str) -> str:
    lowered = question.lower()
    if "forecast" in lowered or "predict" in lowered:
        return "recommend"
    if "why" in lowered or "drop" in lowered or "investigate" in lowered:
        return "investigate"
    return "summarize"


def choose_provider(profile: ModelProfile, task_class: str) -> str:
    providers = normalize_provider_list(profile.providers)
    mode = normalize_model_mode(profile.mode)

    if mode == "local-open":
        return "ollama-local"
    if mode == "byo-cloud":
        if task_class == "investigate":
            return providers[0] if providers else "openai"
        return providers[-1] if providers else "openrouter"
    if providers:
        if task_class == "investigate":
            return providers[0]
        return "ollama-local"
    return "ollama-local"


def estimate_cost_usd(task_class: str, provider: str, chars: int) -> float:
    if provider == "ollama-local":
        return 0.0
    base = {"summarize": 0.0008, "investigate": 0.0032, "recommend": 0.0021}.get(
        task_class, 0.001
    )
    scale = max(chars, 40) / 2200
    return round(base * scale, 6)


def upsert_document_chunks(
    cursor: psycopg.Cursor, workspace_id: str, document_id: str, content: str
) -> None:
    cursor.execute(
        "delete from document_chunks where workspace_id = %s and document_id = %s",
        (workspace_id, document_id),
    )
    chunks = chunk_text(content)
    for index, chunk in enumerate(chunks):
        vector = vector_literal(embedding_for_text(chunk))
        cursor.execute(
            """
            insert into document_chunks (
                id,
                workspace_id,
                document_id,
                chunk_index,
                content,
                embedding
            )
            values (%s, %s, %s, %s, %s, %s::vector)
            """,
            (
                str(uuid.uuid4()),
                workspace_id,
                document_id,
                index,
                chunk,
                vector,
            ),
        )


def retrieve_document_citations(
    cursor: psycopg.Cursor, workspace_id: str, question: str, limit: int = 3
) -> list[dict[str, str]]:
    query_vector = vector_literal(embedding_for_text(question))
    cursor.execute(
        """
        select
            d.title,
            c.content
        from document_chunks c
        inner join business_documents d on d.id = c.document_id
        where c.workspace_id = %s
        order by c.embedding <=> %s::vector
        limit %s
        """,
        (workspace_id, query_vector, limit),
    )
    rows = cursor.fetchall()
    citations: list[dict[str, str]] = []
    for row in rows:
        citations.append(
            {
                "label": f"Document: {row['title']}",
                "detail": str(row["content"]),
                "source": str(row["title"]),
            }
        )
    return citations


def guarded_sql_insight(
    cursor: psycopg.Cursor, workspace_id: str, question: str
) -> str | None:
    lowered = question.lower()
    if "top" in lowered and "product" in lowered and "sell" in lowered:
        cursor.execute(
            """
            select
                sku,
                coalesce(sum(amount_inr), 0)::float as revenue
            from sales_transactions
            where workspace_id = %s
            group by sku
            order by revenue desc
            limit 3
            """,
            (workspace_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            return "No sales rows are available yet for a top-product summary."
        summary = ", ".join(
            f"{row['sku']} ({format_inr_short(to_float(row['revenue']))})"
            for row in rows
        )
        return f"Top selling SKUs by revenue are {summary}."

    if "expense" in lowered and ("highest" in lowered or "spike" in lowered):
        cursor.execute(
            """
            select
                category,
                coalesce(sum(amount_inr), 0)::float as expense_total
            from expense_entries
            where workspace_id = %s
            group by category
            order by expense_total desc
            limit 3
            """,
            (workspace_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            return "No expense rows are available yet for category analysis."
        summary = ", ".join(
            f"{row['category']} ({format_inr_short(to_float(row['expense_total']))})"
            for row in rows
        )
        return f"Highest expense categories right now are {summary}."

    return None


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
            "delete from document_chunks where workspace_id = %s", (workspace_id,)
        )
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
        cursor.execute(
            "delete from action_center_items where workspace_id = %s", (workspace_id,)
        )
        cursor.execute(
            "delete from scheduler_runs where workspace_id = %s", (workspace_id,)
        )

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
        existing = cursor.fetchone()
        if existing is not None:
            document_id = str(existing["id"])
            cursor.execute(
                """
                update business_documents
                set kind = %s, summary = %s
                where id = %s and workspace_id = %s
                """,
                (
                    document["kind"],
                    document["summary"],
                    document_id,
                    workspace_id,
                ),
            )
        else:
            document_id = str(uuid.uuid4())
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
                    document_id,
                    workspace_id,
                    document["title"],
                    document["kind"],
                    document["summary"],
                    document["uploadedAt"],
                ),
            )
        upsert_document_chunks(
            cursor,
            workspace_id,
            document_id,
            document["summary"],
        )

    cursor.execute(
        """
        insert into model_provider_settings (workspace_id, mode, providers, updated_at)
        values (%s, 'local-open', '[]'::jsonb, now())
        on conflict (workspace_id) do nothing
        """,
        (workspace_id,),
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
        if row is not None:
            upsert_document_chunks(
                cursor,
                workspace_id,
                str(row["id"]),
                summary,
            )
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


def load_model_profile_for_cursor(
    cursor: psycopg.Cursor, workspace_id: str
) -> ModelProfile:
    cursor.execute(
        """
        select mode, providers, updated_at
        from model_provider_settings
        where workspace_id = %s
        limit 1
        """,
        (workspace_id,),
    )
    row = cursor.fetchone()
    if row is None:
        now_iso = datetime.utcnow().isoformat() + "Z"
        return ModelProfile(mode="local-open", providers=[], updatedAt=now_iso)
    return ModelProfile(
        mode=normalize_model_mode(str(row["mode"])),
        providers=normalize_provider_list(
            [str(item) for item in (row.get("providers") or [])]
        ),
        updatedAt=row["updated_at"].isoformat(),
    )


def load_model_profile() -> ModelProfile:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        return load_model_profile_for_cursor(cursor, workspace_id)


def save_model_profile(payload: ModelProviderSettings) -> ModelProviderSettingsResponse:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        mode = normalize_model_mode(payload.mode)
        providers = normalize_provider_list(payload.providers)
        cursor.execute(
            """
            insert into model_provider_settings (workspace_id, mode, providers, updated_at)
            values (%s, %s, %s, now())
            on conflict (workspace_id)
            do update set mode = excluded.mode, providers = excluded.providers, updated_at = now()
            returning mode, providers, updated_at
            """,
            (
                workspace_id,
                mode,
                Json(providers),
            ),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Unable to save model provider settings.")
    profile = ModelProfile(
        mode=normalize_model_mode(str(row["mode"])),
        providers=normalize_provider_list(
            [str(item) for item in (row["providers"] or [])]
        ),
        updatedAt=row["updated_at"].isoformat(),
    )
    return ModelProviderSettingsResponse(saved=True, profile=profile)


def due_days(item: RecurringObligation) -> int:
    return (parse_iso_date(item.dueDate) - date.today()).days


def format_action_amount(amount: float) -> str:
    return f"₹{amount:,.0f}"


def map_action_row(row: dict[str, Any]) -> ActionCenterItem:
    return ActionCenterItem(
        id=str(row["id"]),
        title=str(row["title"]),
        detail=str(row["detail"]),
        severity=str(row["severity"]),
        actionType=str(row["action_type"]),
        targetEntity=str(row["target_entity"]),
        status=str(row["status"]),
        snoozedUntil=(str(row["snoozed_until"]) if row.get("snoozed_until") else None),
        resolutionNote=(
            str(row["resolution_note"]) if row.get("resolution_note") else None
        ),
    )


def seed_candidate_actions(
    obligations: list[RecurringObligation], import_ledger: ImportLedgerSnapshot
) -> list[ActionCenterItem]:
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
                    f"{entry.confirmedAt[:10]}. Use this ledger in the next investigation."
                ),
                severity="info",
                actionType="review_import",
                targetEntity=entry.importType,
                status="watching",
            )
        )

    if queue:
        return queue

    return [
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


def sync_action_center(
    cursor: psycopg.Cursor,
    workspace_id: str,
    candidates: list[ActionCenterItem],
) -> list[ActionCenterItem]:
    active_ids = [item.id for item in candidates]
    for item in candidates:
        cursor.execute(
            """
            insert into action_center_items (
                id,
                workspace_id,
                title,
                detail,
                severity,
                action_type,
                target_entity,
                status,
                snoozed_until,
                resolution_note,
                updated_at
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            on conflict (id)
            do update set
                title = excluded.title,
                detail = excluded.detail,
                severity = excluded.severity,
                action_type = excluded.action_type,
                target_entity = excluded.target_entity,
                updated_at = now()
            """,
            (
                item.id,
                workspace_id,
                item.title,
                item.detail,
                item.severity,
                item.actionType,
                item.targetEntity,
                item.status,
                item.snoozedUntil,
                item.resolutionNote,
            ),
        )

    if active_ids:
        cursor.execute(
            """
            delete from action_center_items
            where workspace_id = %s
              and status in ('open', 'watching')
              and not (id = any(%s::varchar[]))
            """,
            (workspace_id, active_ids),
        )

    cursor.execute(
        """
        select
            id,
            title,
            detail,
            severity,
            action_type,
            target_entity,
            status,
            snoozed_until,
            resolution_note
        from action_center_items
        where workspace_id = %s
        order by
            case status
                when 'open' then 0
                when 'watching' then 1
                when 'snoozed' then 2
                else 3
            end,
            updated_at desc
        """,
        (workspace_id,),
    )
    return [map_action_row(row) for row in cursor.fetchall()]


def build_action_queue() -> ActionCenterSnapshot:
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
        obligations = sort_obligations(
            [map_recurring_row(row) for row in cursor.fetchall()]
        )
        import_ledger = build_import_ledger()
        candidates = seed_candidate_actions(obligations, import_ledger)
        queue = sync_action_center(cursor, workspace_id, candidates)

    headline = (
        "Focus first on obligations that can tighten cash, then use the imported ledgers "
        "to validate what changed most recently."
    )
    return ActionCenterSnapshot(headline=headline, items=queue)


def update_action_status(
    action_id: str, payload: ActionStatusUpdateRequest
) -> ActionStatusUpdateResponse:
    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        normalized_status = payload.status.strip().lower()
        if normalized_status not in {"open", "watching", "snoozed", "resolved"}:
            normalized_status = "watching"

        snoozed_until = payload.snoozeUntil if normalized_status == "snoozed" else None
        resolution_note = (
            payload.resolutionNote if normalized_status == "resolved" else None
        )
        cursor.execute(
            """
            update action_center_items
            set
                status = %s,
                snoozed_until = %s,
                resolution_note = %s,
                updated_at = now()
            where id = %s and workspace_id = %s
            returning
                id,
                title,
                detail,
                severity,
                action_type,
                target_entity,
                status,
                snoozed_until,
                resolution_note
            """,
            (
                normalized_status,
                snoozed_until,
                resolution_note,
                action_id,
                workspace_id,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                """
                insert into action_center_items (
                    id,
                    workspace_id,
                    title,
                    detail,
                    severity,
                    action_type,
                    target_entity,
                    status,
                    snoozed_until,
                    resolution_note
                )
                values (%s, %s, %s, %s, 'info', 'manual_review', 'Manual action', %s, %s, %s)
                returning
                    id,
                    title,
                    detail,
                    severity,
                    action_type,
                    target_entity,
                    status,
                    snoozed_until,
                    resolution_note
                """,
                (
                    action_id,
                    workspace_id,
                    "Manual action entry",
                    "Action was manually added during status update.",
                    normalized_status,
                    snoozed_until,
                    resolution_note,
                ),
            )
            row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Unable to update action status.")
    return ActionStatusUpdateResponse(updated=True, item=map_action_row(row))


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
        generatedAt=datetime.utcnow().isoformat() + "Z",
    )


def generate_investigation(question: str) -> InvestigationResult:
    started_at = time.perf_counter()
    refusal = guard_question(question)
    if refusal:
        return InvestigationResult(
            question=question,
            summary=refusal,
            confidence=0.98,
            evidence=[
                {
                    "label": "Guardrail policy",
                    "detail": "Only safe, read-only business analytics prompts are supported.",
                    "source": "query_guardrails",
                }
            ],
            risks=["Unsafe query attempt blocked."],
            recommendations=[
                "Ask business questions such as 'why did profit drop?' or 'top selling SKUs this month'."
            ],
            provider="policy-guard",
            mode="local-open",
            latencyMs=int((time.perf_counter() - started_at) * 1000),
            estimatedCostUsd=0.0,
        )

    ensure_demo_seeded()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        profile = load_model_profile_for_cursor(cursor, workspace_id)
        task_class = infer_task_class(question)
        provider = choose_provider(profile, task_class)
        sql_insight = guarded_sql_insight(cursor, workspace_id, question)
        citations = retrieve_document_citations(cursor, workspace_id, question, limit=2)

        cursor.execute(
            """
            select
                coalesce(sum(amount_inr), 0)::float as revenue_total,
                coalesce(avg(margin_pct), 0)::float as avg_margin
            from sales_transactions
            where workspace_id = %s
            """,
            (workspace_id,),
        )
        revenue_stats = cursor.fetchone() or {"revenue_total": 0.0, "avg_margin": 0.0}
        revenue_total = to_float(revenue_stats["revenue_total"])
        avg_margin = to_float(revenue_stats["avg_margin"])
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

    evidence = [
        {
            "label": "Utility pressure",
            "detail": f"Average utility burden is ₹{utility_avg:,.0f} this cycle.",
            "source": "expense_entries.utilities",
        },
        {
            "label": "Supplier cash pressure",
            "detail": f"₹{upcoming_supplier:,.0f} is the largest upcoming supplier obligation.",
            "source": "recurring_obligations.supplier",
        },
        {
            "label": "Near-expiry risk",
            "detail": f"{near_expiry} product lots are inside the next 45-day near-expiry window.",
            "source": "products.expiry_window_45d",
        },
    ]
    if sql_insight:
        evidence.append(
            {
                "label": "Guarded SQL summary",
                "detail": sql_insight,
                "source": "safe_sql_assistant",
            }
        )
    evidence.extend(citations)

    confidence = 0.82 + (0.04 if citations else 0.0) + (0.03 if sql_insight else 0.0)
    confidence = min(0.96, round(confidence, 2))
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    estimated_cost = estimate_cost_usd(task_class, provider, len(question))

    summary = (
        "Profit pressure is mainly from rising operating costs and near-term supplier cash "
        f"obligations while tracked revenue is {format_inr_short(revenue_total)}."
    )
    if avg_margin < 22:
        summary = (
            "Profit pressure is elevated because margin is slipping below 22% while recurring "
            "supplier and utility costs remain high."
        )

    return InvestigationResult(
        question=question,
        summary=summary,
        confidence=confidence,
        evidence=evidence,
        risks=[
            "Recurring supplier and utility costs can compress short-term cash.",
            "Near-expiry inventory can force discounting and reduce realized margin.",
        ],
        recommendations=[
            "Prioritize near-expiry SKUs in the next local promotion cycle.",
            "Delay low-priority reorders until after high-value supplier dues are cleared.",
            "Review expense categories weekly using the guarded SQL assistant prompts.",
        ],
        provider=provider,
        mode=profile.mode,
        latencyMs=latency_ms,
        estimatedCostUsd=estimated_cost,
    )


def generate_forecast(metric: str, horizon: str) -> ForecastResult:
    ensure_demo_seeded()
    horizon_days = 30
    if horizon.endswith("d") and horizon[:-1].isdigit():
        horizon_days = max(7, min(180, int(horizon[:-1])))

    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]

        cursor.execute(
            """
            select date, coalesce(sum(amount_inr), 0)::float as daily_total
            from sales_transactions
            where workspace_id = %s
            group by date
            order by date asc
            """,
            (workspace_id,),
        )
        sales_rows = cursor.fetchall()
        daily_sales = [to_float(row["daily_total"]) for row in sales_rows]

        cursor.execute(
            """
            select date, coalesce(sum(amount_inr), 0)::float as daily_total
            from purchase_transactions
            where workspace_id = %s
            group by date
            order by date asc
            """,
            (workspace_id,),
        )
        purchase_rows = cursor.fetchall()
        daily_purchases = [to_float(row["daily_total"]) for row in purchase_rows]

        cursor.execute(
            """
            select occurred_on, coalesce(sum(amount_inr), 0)::float as daily_total
            from expense_entries
            where workspace_id = %s
            group by occurred_on
            order by occurred_on asc
            """,
            (workspace_id,),
        )
        expense_rows = cursor.fetchall()
        daily_expenses = [to_float(row["daily_total"]) for row in expense_rows]

        cursor.execute(
            """
            select coalesce(sum(amount_inr), 0)::float as recurring_due
            from recurring_obligations
            where workspace_id = %s and status <> 'paid'
            """,
            (workspace_id,),
        )
        recurring_due = to_float((cursor.fetchone() or {}).get("recurring_due"))

    def moving_average(values: list[float], window: int) -> float:
        if not values:
            return 0.0
        sample = values[-window:] if len(values) >= window else values
        return sum(sample) / len(sample)

    sales_avg = moving_average(daily_sales, 5)
    purchases_avg = moving_average(daily_purchases, 5)
    expenses_avg = moving_average(daily_expenses, 5)
    seasonal_factor = 1.06 if horizon_days <= 45 else 1.03

    metric_key = metric.lower()
    if metric_key not in {"sales", "purchases", "recurring", "cash"}:
        metric_key = "sales"

    if metric_key == "sales":
        projected_low = sales_avg * 0.94
        projected_high = sales_avg * seasonal_factor
        baseline = f"Recent daily sales moving average: {format_inr_short(sales_avg)}"
        projected_range = f"{format_inr_short(projected_low)} to {format_inr_short(projected_high)} per day"
        warnings = [
            "Sales projection assumes similar OTC demand velocity.",
            "Projection drops if near-expiry stock is not rotated faster.",
        ]
    elif metric_key == "purchases":
        projected_low = purchases_avg * 0.88
        projected_high = purchases_avg * 1.08
        baseline = (
            f"Recent daily purchase moving average: {format_inr_short(purchases_avg)}"
        )
        projected_range = f"{format_inr_short(projected_low)} to {format_inr_short(projected_high)} per day"
        warnings = [
            "Higher supplier dues may require staggered procurement.",
            "Underperforming lines should not be reordered at baseline pace.",
        ]
    elif metric_key == "recurring":
        projected_low = recurring_due * 0.95
        projected_high = recurring_due * 1.1
        baseline = (
            f"Current unpaid recurring obligations: {format_inr_short(recurring_due)}"
        )
        projected_range = f"{format_inr_short(projected_low)} to {format_inr_short(projected_high)} in next {horizon_days} days"
        warnings = [
            "Utility and rent changes can widen this band quickly.",
            "Treat supplier obligations as high-priority cash events.",
        ]
    else:
        cash_runway = sales_avg - purchases_avg - expenses_avg
        projected_low = cash_runway * 0.8
        projected_high = cash_runway * 1.15
        baseline = f"Current daily cash delta baseline: {format_inr_short(cash_runway)}"
        projected_range = f"{format_inr_short(projected_low)} to {format_inr_short(projected_high)} per day"
        warnings = [
            "Cash projection assumes recurring dues are managed on time.",
            "Delayed supplier payment can protect cash short term but raise reorder risk.",
        ]

    return ForecastResult(
        metric=metric_key,
        horizon=f"{horizon_days}d",
        baseline=baseline,
        projectedRange=projected_range,
        assumptions=[
            "Moving-average baseline over recent transactional history.",
            "Light seasonality uplift for short-horizon pharmacy demand.",
            "No abrupt structural shift in supplier availability.",
        ],
        warnings=warnings,
    )


def build_scenario_plan(payload: ScenarioPlannerRequest) -> ScenarioPlannerResult:
    forecast_sales = generate_forecast("sales", f"{payload.horizonDays}d")
    forecast_cash = generate_forecast("cash", f"{payload.horizonDays}d")

    summary = "Scenario generated using deterministic baseline deltas."
    deltas: list[ScenarioDelta] = []
    recommendations: list[str] = []

    if payload.scenarioType == "supplier_price_increase":
        summary = f"Supplier price increase scenario at +{payload.percentage:.1f}%."
        deltas = [
            ScenarioDelta(
                metric="Purchase cost",
                baseline=forecast_sales.baseline,
                projected=f"+{payload.percentage:.1f}% relative cost pressure",
                impact="Gross margin compression risk increases.",
            ),
            ScenarioDelta(
                metric="Cash runway",
                baseline=forecast_cash.baseline,
                projected="Lower buffer due to procurement inflation.",
                impact="Prioritize high-turn SKUs only.",
            ),
        ]
        recommendations = [
            "Shift reorder budget toward high-turn and higher-margin SKUs.",
            "Negotiate staggered payment terms on supplier dues.",
        ]
    elif payload.scenarioType == "underperforming_product_line":
        summary = "Underperforming line scenario with slower sell-through."
        deltas = [
            ScenarioDelta(
                metric="Inventory carry",
                baseline="Current carry aligned to recent demand",
                projected=f"Carry risk grows by roughly {payload.percentage:.1f}%",
                impact="Dead stock and expiry risk rises.",
            ),
            ScenarioDelta(
                metric="Margin realization",
                baseline="Current margin trajectory",
                projected="Potential markdown-driven margin erosion.",
                impact="Profit conversion declines.",
            ),
        ]
        recommendations = [
            "Reduce reorder frequency for underperforming categories.",
            "Run targeted movement campaigns for aging lots.",
        ]
    elif payload.scenarioType == "delayed_reorder":
        summary = (
            "Delayed reorder scenario balancing cash protection and stockout risk."
        )
        deltas = [
            ScenarioDelta(
                metric="Short-term cash",
                baseline=forecast_cash.baseline,
                projected=f"Improves by ~{payload.percentage:.1f}% temporarily",
                impact="Cash buffer improves in near term.",
            ),
            ScenarioDelta(
                metric="Stockout probability",
                baseline="Current service level",
                projected="Higher risk for fast-moving SKUs.",
                impact="Potential missed revenue days.",
            ),
        ]
        recommendations = [
            "Delay reorder only for low-turn SKUs.",
            "Protect minimum stock thresholds for high-turn essentials.",
        ]
    else:
        summary = "Rent/electricity increase scenario with fixed-cost pressure."
        deltas = [
            ScenarioDelta(
                metric="Recurring overhead",
                baseline="Current recurring obligation baseline",
                projected=f"+{payload.percentage:.1f}% fixed-cost burden",
                impact="Lower net cash conversion.",
            ),
            ScenarioDelta(
                metric="Break-even threshold",
                baseline="Current daily break-even level",
                projected="Higher required daily revenue.",
                impact="More pressure on margin discipline.",
            ),
        ]
        recommendations = [
            "Review non-essential operating spend for offset opportunities.",
            "Increase focus on better-margin product categories.",
        ]

    return ScenarioPlannerResult(
        scenarioType=payload.scenarioType,
        horizonDays=payload.horizonDays,
        summary=summary,
        deltas=deltas,
        recommendations=recommendations,
    )


def build_scheduler_run() -> SchedulerRunResult:
    ensure_demo_seeded()
    briefing = generate_briefing()
    with db_cursor() as cursor:
        workspace_id = ensure_workspace(cursor)["id"]
        anomaly_count = len(briefing.anomalies)
        due_count = len(briefing.dueToday)
        morning_brief_id = f"brief-{uuid.uuid4().hex[:10]}"
        cursor.execute(
            """
            insert into scheduler_runs (
                id,
                workspace_id,
                morning_brief_id,
                anomaly_count,
                due_reminder_count
            )
            values (%s, %s, %s, %s, %s)
            returning created_at
            """,
            (
                str(uuid.uuid4()),
                workspace_id,
                morning_brief_id,
                anomaly_count,
                due_count,
            ),
        )
        row = cursor.fetchone()
    created_at = row["created_at"].isoformat() if row else datetime.utcnow().isoformat()
    return SchedulerRunResult(
        generatedAt=created_at,
        morningBriefId=morning_brief_id,
        anomalyCount=anomaly_count,
        dueReminderCount=due_count,
    )


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

    if item.status == "snoozed":
        return ActionDraft(
            actionType=item.actionType,
            targetEntity=item.targetEntity,
            rationale="This action is snoozed and should be revalidated before execution.",
            draftText=(
                f"Before acting on {item.targetEntity}, re-check whether the original trigger "
                f"still applies and unsnooze if it is still operationally relevant."
            ),
            approvalRequired=True,
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
