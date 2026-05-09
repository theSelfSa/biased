from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "biased-api"


class ImportPreview(BaseModel):
    importType: str
    filename: str
    rowCount: int
    columns: list[str]
    inferredMappings: dict[str, str]
    warnings: list[str] = Field(default_factory=list)


class ImportJobResponse(BaseModel):
    jobId: str
    preview: ImportPreview


class InvestigationRequest(BaseModel):
    question: str


class InvestigationEvidence(BaseModel):
    label: str
    detail: str
    source: str


class InvestigationResult(BaseModel):
    question: str
    summary: str
    confidence: float
    evidence: list[InvestigationEvidence]
    risks: list[str]
    recommendations: list[str]


class BriefingRequest(BaseModel):
    mode: str = "demo"


class BriefingResult(BaseModel):
    headline: str
    items: list[str]
    dueToday: list[str]
    anomalies: list[str]
    suggestedActions: list[str]


class ForecastRequest(BaseModel):
    metric: str = "sales"
    horizon: str = "30d"


class ForecastResult(BaseModel):
    metric: str
    horizon: str
    baseline: str
    projectedRange: str
    assumptions: list[str]
    warnings: list[str]


class ActionDraft(BaseModel):
    actionType: str
    targetEntity: str
    rationale: str
    draftText: str
    approvalRequired: bool


class ModelProviderSettings(BaseModel):
    mode: str
    providers: list[str] = Field(default_factory=list)
