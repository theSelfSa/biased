import {
  boolean,
  integer,
  jsonb,
  numeric,
  pgTable,
  text,
  timestamp,
  uuid,
  varchar,
} from "drizzle-orm/pg-core";

export const businessWorkspaces = pgTable("business_workspaces", {
  id: uuid("id").defaultRandom().primaryKey(),
  name: varchar("name", { length: 160 }).notNull(),
  slug: varchar("slug", { length: 160 }).notNull().unique(),
  market: varchar("market", { length: 64 }).notNull().default("india"),
  industry: varchar("industry", { length: 64 }).notNull().default("pharmacy"),
  baseCurrency: varchar("base_currency", { length: 8 }).notNull().default("INR"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export const workspaceMembers = pgTable("workspace_members", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  userId: text("user_id").notNull(),
  role: varchar("role", { length: 32 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const suppliers = pgTable("suppliers", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  name: varchar("name", { length: 160 }).notNull(),
  category: varchar("category", { length: 120 }).notNull(),
  preferredLeadDays: integer("preferred_lead_days").notNull().default(3),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const products = pgTable("products", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  sku: varchar("sku", { length: 64 }).notNull(),
  name: varchar("name", { length: 160 }).notNull(),
  category: varchar("category", { length: 120 }).notNull(),
  unitPriceInr: numeric("unit_price_inr", { precision: 10, scale: 2 })
    .notNull()
    .default("0"),
  quantityOnHand: integer("quantity_on_hand").notNull().default(0),
  isColdChain: boolean("is_cold_chain").notNull().default(false),
  expiresOn: text("expires_on"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const expenseEntries = pgTable("expense_entries", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  label: varchar("label", { length: 160 }).notNull(),
  category: varchar("category", { length: 120 }).notNull(),
  amountInr: numeric("amount_inr", { precision: 10, scale: 2 }).notNull(),
  occurredOn: text("occurred_on").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const recurringObligations = pgTable("recurring_obligations", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  label: varchar("label", { length: 160 }).notNull(),
  category: varchar("category", { length: 120 }).notNull(),
  amountInr: numeric("amount_inr", { precision: 10, scale: 2 }).notNull(),
  dueDate: text("due_date").notNull(),
  recurrence: varchar("recurrence", { length: 32 }).notNull(),
  status: varchar("status", { length: 32 }).notNull().default("due"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const salesTransactions = pgTable("sales_transactions", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  date: text("date").notNull(),
  sku: varchar("sku", { length: 64 }).notNull(),
  name: varchar("name", { length: 160 }),
  category: varchar("category", { length: 120 }),
  quantity: integer("quantity").notNull().default(0),
  amountInr: numeric("amount_inr", { precision: 12, scale: 2 }).notNull().default("0"),
  marginPct: numeric("margin_pct", { precision: 6, scale: 2 }),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const purchaseTransactions = pgTable("purchase_transactions", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  date: text("date").notNull(),
  supplierName: varchar("supplier_name", { length: 160 }).notNull(),
  sku: varchar("sku", { length: 64 }).notNull(),
  quantity: integer("quantity").notNull().default(0),
  amountInr: numeric("amount_inr", { precision: 12, scale: 2 }).notNull().default("0"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const businessDocuments = pgTable("business_documents", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  title: varchar("title", { length: 240 }).notNull(),
  kind: varchar("kind", { length: 64 }).notNull(),
  summary: text("summary").notNull(),
  uploadedAt: text("uploaded_at").notNull(),
  stored: boolean("stored").notNull().default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const importJobs = pgTable("import_jobs", {
  id: uuid("id").defaultRandom().primaryKey(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  importType: varchar("import_type", { length: 64 }).notNull(),
  filename: varchar("filename", { length: 240 }).notNull(),
  rowCount: integer("row_count").notNull().default(0),
  inferredMappings: jsonb("inferred_mappings").notNull().default({}),
  warnings: jsonb("warnings").notNull().default([]),
  status: varchar("status", { length: 32 }).notNull().default("pending"),
  appliedCount: integer("applied_count").notNull().default(0),
  affectedCollections: jsonb("affected_collections").notNull().default([]),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  confirmedAt: timestamp("confirmed_at", { withTimezone: true }),
});

export const importJobRows = pgTable("import_job_rows", {
  id: uuid("id").defaultRandom().primaryKey(),
  jobId: uuid("job_id")
    .references(() => importJobs.id, { onDelete: "cascade" })
    .notNull(),
  workspaceId: uuid("workspace_id")
    .references(() => businessWorkspaces.id, { onDelete: "cascade" })
    .notNull(),
  rowIndex: integer("row_index").notNull(),
  payload: jsonb("payload").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});
