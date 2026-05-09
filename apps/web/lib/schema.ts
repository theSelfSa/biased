import {
  boolean,
  integer,
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
