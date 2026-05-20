import { z } from "zod";

export const memberRoleSchema = z.enum(["owner", "manager", "accountant"]);
export type MemberRole = z.infer<typeof memberRoleSchema>;

export const recurrenceSchema = z.enum(["monthly", "quarterly", "annual"]);
export type Recurrence = z.infer<typeof recurrenceSchema>;

export const recurringObligationStatusSchema = z.enum([
  "due",
  "paid",
  "scheduled",
]);
export type RecurringObligationStatus = z.infer<
  typeof recurringObligationStatusSchema
>;

export const supplierSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  preferredLeadDays: z.number(),
});
export type Supplier = z.infer<typeof supplierSchema>;

export const productSchema = z.object({
  id: z.string(),
  sku: z.string(),
  name: z.string(),
  category: z.string(),
  unitPriceInr: z.number(),
  quantityOnHand: z.number(),
  expiresOn: z.string().optional(),
});
export type Product = z.infer<typeof productSchema>;

export const recurringObligationSchema = z.object({
  id: z.string(),
  label: z.string(),
  category: z.string(),
  amountInr: z.number(),
  dueDate: z.string(),
  recurrence: recurrenceSchema,
  status: recurringObligationStatusSchema,
});
export type RecurringObligation = z.infer<typeof recurringObligationSchema>;

export const createRecurringObligationInputSchema = recurringObligationSchema
  .omit({ id: true })
  .extend({
    status: recurringObligationStatusSchema.optional(),
  });
export type CreateRecurringObligationInput = z.infer<
  typeof createRecurringObligationInputSchema
>;

export const updateRecurringObligationStatusInputSchema = z.object({
  status: recurringObligationStatusSchema,
});
export type UpdateRecurringObligationStatusInput = z.infer<
  typeof updateRecurringObligationStatusInputSchema
>;

export const salesTransactionSchema = z.object({
  id: z.string(),
  date: z.string(),
  sku: z.string(),
  name: z.string().nullable().optional(),
  category: z.string().nullable().optional(),
  quantity: z.number().int(),
  amountInr: z.number(),
  marginPct: z.number().nullable().optional(),
});
export type SalesTransaction = z.infer<typeof salesTransactionSchema>;

export const purchaseTransactionSchema = z.object({
  id: z.string(),
  date: z.string(),
  supplierName: z.string(),
  sku: z.string(),
  quantity: z.number().int(),
  amountInr: z.number(),
});
export type PurchaseTransaction = z.infer<typeof purchaseTransactionSchema>;

export const expenseEntrySchema = z.object({
  id: z.string(),
  occurredOn: z.string(),
  label: z.string(),
  category: z.string(),
  amountInr: z.number(),
});
export type ExpenseEntry = z.infer<typeof expenseEntrySchema>;

export const quickAddSaleInputSchema = salesTransactionSchema
  .omit({ id: true })
  .extend({
    quantity: z.number().int().min(1),
    amountInr: z.number().nonnegative(),
    marginPct: z.number().min(0).max(100).nullable().optional(),
  });
export type QuickAddSaleInput = z.infer<typeof quickAddSaleInputSchema>;

export const quickAddPurchaseInputSchema = purchaseTransactionSchema
  .omit({ id: true })
  .extend({
    quantity: z.number().int().min(1),
    amountInr: z.number().nonnegative(),
  });
export type QuickAddPurchaseInput = z.infer<typeof quickAddPurchaseInputSchema>;

export const quickAddExpenseInputSchema = expenseEntrySchema
  .omit({ id: true })
  .extend({
    amountInr: z.number().nonnegative(),
  });
export type QuickAddExpenseInput = z.infer<typeof quickAddExpenseInputSchema>;

export const statCardSchema = z.object({
  label: z.string(),
  value: z.string(),
  delta: z.string(),
  tone: z.enum(["positive", "neutral", "warning", "critical"]),
});
export type StatCard = z.infer<typeof statCardSchema>;

export const insightSchema = z.object({
  id: z.string(),
  title: z.string(),
  detail: z.string(),
  severity: z.enum(["info", "warning", "critical"]),
});
export type Insight = z.infer<typeof insightSchema>;

export const dashboardSnapshotSchema = z.object({
  workspaceName: z.string(),
  subtitle: z.string(),
  stats: z.array(statCardSchema),
  marginSeries: z.array(
    z.object({
      label: z.string(),
      revenueInr: z.number(),
      marginPct: z.number(),
    }),
  ),
  obligations: z.array(recurringObligationSchema),
  inventoryAlerts: z.array(insightSchema),
  actionQueue: z.array(insightSchema),
});
export type DashboardSnapshot = z.infer<typeof dashboardSnapshotSchema>;

export const businessDocumentSchema = z.object({
  id: z.string(),
  title: z.string(),
  kind: z.string(),
  summary: z.string(),
  uploadedAt: z.string(),
});
export type BusinessDocument = z.infer<typeof businessDocumentSchema>;

export const documentUploadResponseSchema = businessDocumentSchema.extend({
  stored: z.boolean().default(true),
});
export type DocumentUploadResponse = z.infer<
  typeof documentUploadResponseSchema
>;
export const investigationToolCallSchema = z.object({
  tool: z.string(),
  status: z.string(),
  runtime: z.string(),
  detail: z.string().optional(),
});
export type InvestigationToolCall = z.infer<typeof investigationToolCallSchema>;

export const investigationOrchestrationSchema = z.object({
  framework: z.string(),
  route: z.array(z.string()),
  taskClass: z.string(),
  toolRuntime: z.string(),
  toolCalls: z.array(investigationToolCallSchema),
});
export type InvestigationOrchestration = z.infer<
  typeof investigationOrchestrationSchema
>;

export const investigationResultSchema = z.object({
  question: z.string(),
  summary: z.string(),
  confidence: z.number().min(0).max(1),
  evidence: z.array(
    z.object({
      label: z.string(),
      detail: z.string(),
      source: z.string(),
    }),
  ),
  risks: z.array(z.string()),
  recommendations: z.array(z.string()),
  provider: z.string().optional(),
  mode: z.enum(["local-open", "byo-cloud", "hybrid"]).optional(),
  latencyMs: z.number().int().optional(),
  estimatedCostUsd: z.number().min(0).optional(),
  orchestration: investigationOrchestrationSchema.optional(),
});
export type InvestigationResult = z.infer<typeof investigationResultSchema>;

export const briefingResultSchema = z.object({
  headline: z.string(),
  items: z.array(z.string()),
  dueToday: z.array(z.string()),
  anomalies: z.array(z.string()),
  suggestedActions: z.array(z.string()),
  generatedAt: z.string().optional(),
});
export type BriefingResult = z.infer<typeof briefingResultSchema>;

export const forecastResultSchema = z.object({
  metric: z.string(),
  horizon: z.string(),
  baseline: z.string(),
  projectedRange: z.string(),
  assumptions: z.array(z.string()),
  warnings: z.array(z.string()),
});
export type ForecastResult = z.infer<typeof forecastResultSchema>;

export const actionDraftSchema = z.object({
  actionType: z.string(),
  targetEntity: z.string(),
  rationale: z.string(),
  draftText: z.string(),
  approvalRequired: z.boolean(),
});
export type ActionDraft = z.infer<typeof actionDraftSchema>;

export const actionCenterItemSchema = insightSchema.extend({
  actionType: z.string(),
  targetEntity: z.string(),
  status: z.enum(["open", "watching", "snoozed", "resolved"]),
  snoozedUntil: z.string().nullable().optional(),
  resolutionNote: z.string().nullable().optional(),
});
export type ActionCenterItem = z.infer<typeof actionCenterItemSchema>;

export const actionCenterSnapshotSchema = z.object({
  headline: z.string(),
  items: z.array(actionCenterItemSchema),
});
export type ActionCenterSnapshot = z.infer<typeof actionCenterSnapshotSchema>;

export const importPreviewSchema = z.object({
  importType: z.string(),
  filename: z.string(),
  rowCount: z.number(),
  columns: z.array(z.string()),
  inferredMappings: z.record(z.string(), z.string()),
  warnings: z.array(z.string()),
});
export type ImportPreview = z.infer<typeof importPreviewSchema>;

export const importConfirmResponseSchema = z.object({
  status: z.enum(["confirmed", "missing", "already_confirmed"]),
  jobId: z.string(),
  importType: z.string().optional(),
  rowCount: z.number().default(0),
  appliedCount: z.number().default(0),
  affectedCollections: z.array(z.string()).default([]),
  warnings: z.array(z.string()).default([]),
});
export type ImportConfirmResponse = z.infer<typeof importConfirmResponseSchema>;

export const importHistoryEntrySchema = z.object({
  jobId: z.string(),
  importType: z.string(),
  filename: z.string(),
  rowCount: z.number(),
  appliedCount: z.number(),
  confirmedAt: z.string(),
});
export type ImportHistoryEntry = z.infer<typeof importHistoryEntrySchema>;

export const importCollectionSummarySchema = z.object({
  importType: z.string(),
  rowCount: z.number(),
  latestImportAt: z.string().nullable(),
  columns: z.array(z.string()),
  sampleRows: z.array(z.record(z.string(), z.unknown())),
});
export type ImportCollectionSummary = z.infer<
  typeof importCollectionSummarySchema
>;

export const importLedgerSnapshotSchema = z.object({
  history: z.array(importHistoryEntrySchema),
  collections: z.array(importCollectionSummarySchema),
});
export type ImportLedgerSnapshot = z.infer<typeof importLedgerSnapshotSchema>;

export const modelProviderModeSchema = z.enum([
  "local-open",
  "byo-cloud",
  "hybrid",
]);
export type ModelProviderMode = z.infer<typeof modelProviderModeSchema>;

export const modelProfileSchema = z.object({
  mode: modelProviderModeSchema,
  providers: z.array(z.string()),
  updatedAt: z.string(),
});
export type ModelProfile = z.infer<typeof modelProfileSchema>;

export const modelProviderSettingsInputSchema = z.object({
  mode: modelProviderModeSchema,
  providers: z.array(z.string()),
});
export type ModelProviderSettingsInput = z.infer<
  typeof modelProviderSettingsInputSchema
>;

export const modelProviderSettingsResponseSchema = z.object({
  saved: z.boolean(),
  profile: modelProfileSchema,
});
export type ModelProviderSettingsResponse = z.infer<
  typeof modelProviderSettingsResponseSchema
>;

export const actionStatusUpdateInputSchema = z.object({
  status: z.enum(["open", "watching", "snoozed", "resolved"]),
  snoozeUntil: z.string().optional(),
  resolutionNote: z.string().optional(),
});
export type ActionStatusUpdateInput = z.infer<
  typeof actionStatusUpdateInputSchema
>;

export const actionStatusUpdateResponseSchema = z.object({
  updated: z.boolean(),
  item: actionCenterItemSchema,
});
export type ActionStatusUpdateResponse = z.infer<
  typeof actionStatusUpdateResponseSchema
>;

export const scenarioPlannerRequestSchema = z.object({
  scenarioType: z.enum([
    "supplier_price_increase",
    "underperforming_product_line",
    "delayed_reorder",
    "rent_electricity_increase",
  ]),
  horizonDays: z.number().int().min(7).max(180).default(30),
  percentage: z.number().min(0).max(100).default(10),
});
export type ScenarioPlannerRequest = z.infer<
  typeof scenarioPlannerRequestSchema
>;

export const scenarioDeltaSchema = z.object({
  metric: z.string(),
  baseline: z.string(),
  projected: z.string(),
  impact: z.string(),
});
export type ScenarioDelta = z.infer<typeof scenarioDeltaSchema>;

export const scenarioPlannerResultSchema = z.object({
  scenarioType: scenarioPlannerRequestSchema.shape.scenarioType,
  horizonDays: z.number(),
  summary: z.string(),
  deltas: z.array(scenarioDeltaSchema),
  recommendations: z.array(z.string()),
});
export type ScenarioPlannerResult = z.infer<typeof scenarioPlannerResultSchema>;

export const schedulerRunResultSchema = z.object({
  generatedAt: z.string(),
  morningBriefId: z.string(),
  anomalyCount: z.number().int(),
  dueReminderCount: z.number().int(),
});
export type SchedulerRunResult = z.infer<typeof schedulerRunResultSchema>;
