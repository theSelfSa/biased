import { z } from "zod";

export const memberRoleSchema = z.enum(["owner", "manager", "accountant"]);
export type MemberRole = z.infer<typeof memberRoleSchema>;

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
  recurrence: z.enum(["monthly", "quarterly", "annual"]),
  status: z.enum(["due", "paid", "scheduled"]),
});
export type RecurringObligation = z.infer<typeof recurringObligationSchema>;

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
});
export type InvestigationResult = z.infer<typeof investigationResultSchema>;

export const briefingResultSchema = z.object({
  headline: z.string(),
  items: z.array(z.string()),
  dueToday: z.array(z.string()),
  anomalies: z.array(z.string()),
  suggestedActions: z.array(z.string()),
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

export const importPreviewSchema = z.object({
  importType: z.string(),
  filename: z.string(),
  rowCount: z.number(),
  columns: z.array(z.string()),
  inferredMappings: z.record(z.string(), z.string()),
  warnings: z.array(z.string()),
});
export type ImportPreview = z.infer<typeof importPreviewSchema>;
