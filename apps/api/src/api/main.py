from __future__ import annotations

from datetime import date

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.models import (
    ActionDraft,
    ActionCenterSnapshot,
    ActionStatusUpdateRequest,
    ActionStatusUpdateResponse,
    BriefingRequest,
    BriefingResult,
    BusinessDocument,
    CreateRecurringObligationRequest,
    ExpenseEntry,
    ForecastResult,
    ForecastRequest,
    HealthResponse,
    ImportConfirmResponse,
    ImportLedgerSnapshot,
    ImportJobResponse,
    InvestigationRequest,
    InvestigationResult,
    ModelProfile,
    ModelProviderSettings,
    ModelProviderSettingsResponse,
    PurchaseTransaction,
    QuickAddExpenseRequest,
    QuickAddPurchaseRequest,
    QuickAddSaleRequest,
    RecurringObligation,
    ScenarioPlannerRequest,
    ScenarioPlannerResult,
    SchedulerRunResult,
    SalesTransaction,
    UpdateRecurringObligationStatusRequest,
)
from api.services.demo_data import (
    build_scenario_plan,
    build_scheduler_run,
    create_recurring_obligation,
    confirm_import_job,
    draft_action,
    build_action_queue,
    build_import_ledger,
    generate_briefing,
    generate_forecast,
    generate_investigation,
    load_dashboard,
    load_documents,
    load_recurring_obligations,
    mark_recurring_obligation_status,
    load_model_profile,
    save_model_profile,
    preview_upload,
    quick_add_expense,
    quick_add_purchase,
    quick_add_sale,
    store_document,
    store_import_job,
    update_action_status,
)

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse()


@app.get("/api/dashboard")
def dashboard():
    return load_dashboard()


@app.get("/api/import-records", response_model=ImportLedgerSnapshot)
def import_records() -> ImportLedgerSnapshot:
    return build_import_ledger()


@app.get("/api/documents", response_model=list[BusinessDocument])
def documents() -> list[BusinessDocument]:
    return load_documents()


@app.post("/api/documents", response_model=BusinessDocument)
async def upload_document(kind: str = Form("document"), file: UploadFile = File(...)):
    content = await file.read()
    return store_document(
        kind, file.filename or f"upload-{date.today().isoformat()}", content
    )


@app.get("/api/recurring-obligations", response_model=list[RecurringObligation])
def recurring_obligations() -> list[RecurringObligation]:
    return load_recurring_obligations()


@app.post("/api/recurring-obligations", response_model=RecurringObligation)
def create_obligation(
    payload: CreateRecurringObligationRequest,
) -> RecurringObligation:
    return create_recurring_obligation(payload)


@app.post(
    "/api/recurring-obligations/{obligation_id}/mark-paid",
    response_model=RecurringObligation,
)
def mark_obligation(
    obligation_id: str,
    payload: UpdateRecurringObligationStatusRequest,
) -> RecurringObligation:
    obligation = mark_recurring_obligation_status(obligation_id, payload.status)
    if obligation is None:
        raise HTTPException(status_code=404, detail="Recurring obligation not found.")
    return obligation


@app.post("/api/import-jobs", response_model=ImportJobResponse)
async def create_import_job(
    importType: str = Form(...),
    file: UploadFile = File(...),
) -> ImportJobResponse:
    content = await file.read()
    preview, rows = preview_upload(importType, file.filename or "upload.csv", content)
    job_id = store_import_job(preview, rows)
    return ImportJobResponse(jobId=job_id, preview=preview)


@app.post("/api/import-jobs/{job_id}/confirm", response_model=ImportConfirmResponse)
def confirm_job(job_id: str) -> ImportConfirmResponse:
    return confirm_import_job(job_id)


@app.post("/api/investigations", response_model=InvestigationResult)
def investigate(payload: InvestigationRequest) -> InvestigationResult:
    return generate_investigation(payload.question)


@app.post("/api/briefings/generate", response_model=BriefingResult)
def briefing(_: BriefingRequest) -> BriefingResult:
    return generate_briefing()


@app.post("/api/forecasts/run", response_model=ForecastResult)
def forecast(payload: ForecastRequest) -> ForecastResult:
    return generate_forecast(payload.metric, payload.horizon)


@app.post("/api/actions/{action_id}/draft", response_model=ActionDraft)
def action_draft(action_id: str) -> ActionDraft:
    return draft_action(action_id)


@app.post("/api/actions/{action_id}/status", response_model=ActionStatusUpdateResponse)
def action_status_update(
    action_id: str, payload: ActionStatusUpdateRequest
) -> ActionStatusUpdateResponse:
    return update_action_status(action_id, payload)


@app.get("/api/actions", response_model=ActionCenterSnapshot)
def actions() -> ActionCenterSnapshot:
    return build_action_queue()


@app.post("/api/quick-add/sales", response_model=SalesTransaction)
def quick_sale(payload: QuickAddSaleRequest) -> SalesTransaction:
    return quick_add_sale(payload)


@app.post("/api/quick-add/purchases", response_model=PurchaseTransaction)
def quick_purchase(payload: QuickAddPurchaseRequest) -> PurchaseTransaction:
    return quick_add_purchase(payload)


@app.post("/api/quick-add/expenses", response_model=ExpenseEntry)
def quick_expense(payload: QuickAddExpenseRequest) -> ExpenseEntry:
    return quick_add_expense(payload)


@app.post("/api/settings/model-providers", response_model=ModelProviderSettingsResponse)
def model_providers(payload: ModelProviderSettings) -> ModelProviderSettingsResponse:
    return save_model_profile(payload)


@app.get("/api/settings/model-providers", response_model=ModelProfile)
def get_model_providers() -> ModelProfile:
    return load_model_profile()


@app.post("/api/scenarios/run", response_model=ScenarioPlannerResult)
def run_scenario(payload: ScenarioPlannerRequest) -> ScenarioPlannerResult:
    return build_scenario_plan(payload)


@app.post("/api/scheduler/run", response_model=SchedulerRunResult)
def run_scheduler() -> SchedulerRunResult:
    return build_scheduler_run()


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
