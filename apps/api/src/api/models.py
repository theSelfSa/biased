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
    provider: str | None = None
    mode: str | None = None
    latencyMs: int | None = None
    estimatedCostUsd: float | None = None


class BriefingRequest(BaseModel):
    mode: str = "demo"


class BriefingResult(BaseModel):
    headline: str
    items: list[str]
    dueToday: list[str]
    anomalies: list[str]
    suggestedActions: list[str]
    generatedAt: str | None = None


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
    snoozedUntil: str | None = None
    resolutionNote: str | None = None


class ActionCenterSnapshot(BaseModel):
    headline: str
    items: list[ActionCenterItem] = Field(default_factory=list)


class ModelProviderSettings(BaseModel):
    mode: str
    providers: list[str] = Field(default_factory=list)


class ModelProfile(BaseModel):
    mode: str
    providers: list[str] = Field(default_factory=list)
    updatedAt: str


class ModelProviderSettingsResponse(BaseModel):
    saved: bool
    profile: ModelProfile


class SalesTransaction(BaseModel):
    id: str
    date: str
    sku: str
    name: str | None = None
    category: str | None = None
    quantity: int
    amountInr: float
    marginPct: float | None = None


class PurchaseTransaction(BaseModel):
    id: str
    date: str
    supplierName: str
    sku: str
    quantity: int
    amountInr: float


class ExpenseEntry(BaseModel):
    id: str
    occurredOn: str
    label: str
    category: str
    amountInr: float


class QuickAddSaleRequest(BaseModel):
    date: str
    sku: str
    name: str | None = None
    category: str | None = None
    quantity: int = Field(default=1, ge=1)
    amountInr: float = Field(ge=0)
    marginPct: float | None = Field(default=None, ge=0, le=100)


class QuickAddPurchaseRequest(BaseModel):
    date: str
    supplierName: str
    sku: str
    quantity: int = Field(default=1, ge=1)
    amountInr: float = Field(ge=0)


class QuickAddExpenseRequest(BaseModel):
    occurredOn: str
    label: str
    category: str
    amountInr: float = Field(ge=0)


class ActionStatusUpdateRequest(BaseModel):
    status: str
    snoozeUntil: str | None = None
    resolutionNote: str | None = None


class ActionStatusUpdateResponse(BaseModel):
    updated: bool
    item: ActionCenterItem


class ScenarioPlannerRequest(BaseModel):
    scenarioType: str
    horizonDays: int = Field(default=30, ge=7, le=180)
    percentage: float = Field(default=10, ge=0, le=100)


class ScenarioDelta(BaseModel):
    metric: str
    baseline: str
    projected: str
    impact: str


class ScenarioPlannerResult(BaseModel):
    scenarioType: str
    horizonDays: int
    summary: str
    deltas: list[ScenarioDelta]
    recommendations: list[str]


class SchedulerRunResult(BaseModel):
    generatedAt: str
    morningBriefId: str
    anomalyCount: int
    dueReminderCount: int
