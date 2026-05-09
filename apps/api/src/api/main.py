from __future__ import annotations

from datetime import date

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.models import (
    ActionDraft,
    BriefingRequest,
    BriefingResult,
    ForecastRequest,
    HealthResponse,
    ImportJobResponse,
    InvestigationRequest,
    InvestigationResult,
    ModelProviderSettings,
)
from api.services.demo_data import (
    confirm_import_job,
    document_summary,
    draft_action,
    generate_briefing,
    generate_forecast,
    generate_investigation,
    load_dashboard,
    load_documents,
    preview_upload,
    store_import_job,
)

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
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


@app.get("/api/documents")
def documents():
    return load_documents()


@app.post("/api/documents")
async def upload_document(kind: str = Form("document"), file: UploadFile = File(...)):
    content = await file.read()
    return {
        "id": f"upload-{file.filename}",
        "title": file.filename,
        "kind": kind,
        "summary": document_summary(file.filename, content),
        "uploadedAt": date.today().isoformat(),
    }


@app.post("/api/import-jobs", response_model=ImportJobResponse)
async def create_import_job(
    importType: str = Form(...),
    file: UploadFile = File(...),
) -> ImportJobResponse:
    content = await file.read()
    preview = preview_upload(importType, file.filename or "upload.csv", content)
    job_id = store_import_job(preview)
    return ImportJobResponse(jobId=job_id, preview=preview)


@app.post("/api/import-jobs/{job_id}/confirm")
def confirm_job(job_id: str):
    return confirm_import_job(job_id)


@app.post("/api/investigations", response_model=InvestigationResult)
def investigate(payload: InvestigationRequest) -> InvestigationResult:
    return generate_investigation(payload.question)


@app.post("/api/briefings/generate", response_model=BriefingResult)
def briefing(_: BriefingRequest) -> BriefingResult:
    return generate_briefing()


@app.post("/api/forecasts/run")
def forecast(payload: ForecastRequest):
    return generate_forecast(payload.metric, payload.horizon)


@app.post("/api/actions/{action_id}/draft", response_model=ActionDraft)
def action_draft(action_id: str) -> ActionDraft:
    return draft_action(action_id)


@app.post("/api/settings/model-providers")
def model_providers(payload: ModelProviderSettings):
    return {
        "saved": True,
        "mode": payload.mode,
        "providers": payload.providers,
    }


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
