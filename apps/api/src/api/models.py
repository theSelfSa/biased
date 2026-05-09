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


class ImportConfirmResponse(BaseModel):
    status: str
    jobId: str
    importType: str | None = None
    rowCount: int = 0
    appliedCount: int = 0
    affectedCollections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ImportHistoryEntry(BaseModel):
    jobId: str
    importType: str
    filename: str
    rowCount: int
    appliedCount: int
    confirmedAt: str


class ImportCollectionSummary(BaseModel):
    importType: str
    rowCount: int
    latestImportAt: str | None = None
    columns: list[str] = Field(default_factory=list)
    sampleRows: list[dict[str, object]] = Field(default_factory=list)


class ImportLedgerSnapshot(BaseModel):
    history: list[ImportHistoryEntry] = Field(default_factory=list)
    collections: list[ImportCollectionSummary] = Field(default_factory=list)


class InvestigationRequest(BaseModel):
    question: str


class BusinessDocument(BaseModel):
    id: str
    title: str
    kind: str
    summary: str
    uploadedAt: str
    stored: bool = True


class RecurringObligation(BaseModel):
    id: str
    label: str
    category: str
    amountInr: float
    dueDate: str
    recurrence: str
    status: str


class CreateRecurringObligationRequest(BaseModel):
    label: str
    category: str
    amountInr: float
    dueDate: str
    recurrence: str
    status: str = "due"


class UpdateRecurringObligationStatusRequest(BaseModel):
    status: str = "paid"


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


class ActionCenterItem(BaseModel):
    id: str
    title: str
    detail: str
    severity: str
    actionType: str
    targetEntity: str
    status: str


class ActionCenterSnapshot(BaseModel):
    headline: str
    items: list[ActionCenterItem] = Field(default_factory=list)


class ModelProviderSettings(BaseModel):
    mode: str
    providers: list[str] = Field(default_factory=list)
