import type {
  ActionCenterSnapshot,
  BriefingResult,
  BusinessDocument,
  DashboardSnapshot,
  ImportLedgerSnapshot,
  InvestigationResult,
} from "@biased/contracts";

export const fallbackDashboard: DashboardSnapshot = {
  workspaceName: "Swasthya Care Pharmacy",
  subtitle:
    "Owner command center for margin, stock, and recurring obligations.",
  stats: [
    {
      label: "Monthly revenue",
      value: "₹8.4L",
      delta: "+12.5% vs last month",
      tone: "positive",
    },
    {
      label: "Gross margin",
      value: "23.8%",
      delta: "-1.9 pts on chronic care SKUs",
      tone: "warning",
    },
    {
      label: "Bills due in 10 days",
      value: "₹1.27L",
      delta: "Rent, electricity, distributor payment",
      tone: "critical",
    },
    {
      label: "Near-expiry inventory",
      value: "₹48K",
      delta: "11 lots expiring within 45 days",
      tone: "warning",
    },
  ],
  marginSeries: [
    { label: "Jan", revenueInr: 640000, marginPct: 24.9 },
    { label: "Feb", revenueInr: 675000, marginPct: 24.4 },
    { label: "Mar", revenueInr: 702000, marginPct: 24.1 },
    { label: "Apr", revenueInr: 731000, marginPct: 23.9 },
    { label: "May", revenueInr: 790000, marginPct: 23.6 },
    { label: "Jun", revenueInr: 840000, marginPct: 23.8 },
  ],
  obligations: [
    {
      id: "rent",
      label: "Shop rent",
      category: "Facility",
      amountInr: 55000,
      dueDate: "2026-05-11",
      recurrence: "monthly",
      status: "due",
    },
    {
      id: "power",
      label: "Electricity bill",
      category: "Utilities",
      amountInr: 18200,
      dueDate: "2026-05-14",
      recurrence: "monthly",
      status: "due",
    },
    {
      id: "supplier",
      label: "Primary distributor payment",
      category: "Supplier",
      amountInr: 53800,
      dueDate: "2026-05-16",
      recurrence: "monthly",
      status: "scheduled",
    },
  ],
  inventoryAlerts: [
    {
      id: "expiry-1",
      title: "Cefixime suspension lots need action",
      detail:
        "3 lots expire in 32-41 days and are moving slower than forecast.",
      severity: "warning",
    },
    {
      id: "stock-1",
      title: "Paracetamol syrup is moving 18% faster",
      detail:
        "Demand increased after recent flu wave. Reorder threshold hits in 6 days.",
      severity: "info",
    },
  ],
  actionQueue: [
    {
      id: "act-1",
      title: "Reduce June reorder for low-turn dermatology SKUs",
      detail:
        "Projected overstock value: ₹21K if current purchase pattern continues.",
      severity: "critical",
    },
    {
      id: "act-2",
      title: "Draft distributor negotiation message",
      detail:
        "Electricity and rent increases are compressing cash outlook this cycle.",
      severity: "warning",
    },
  ],
};

export const fallbackBriefing: BriefingResult = {
  headline: "Cash is stable, but margin is softening on chronic care products.",
  items: [
    "Yesterday closed at ₹28.4K sales with stronger OTC demand.",
    "Gross margin slipped because insulin cooler electricity costs rose 14%.",
    "Two dermatology products are underperforming against reorder pace.",
  ],
  dueToday: [
    "Confirm shop rent payment by 4pm",
    "Review distributor invoice variance",
  ],
  anomalies: ["Utility cost spike", "Slow movement on expiring cefixime stock"],
  suggestedActions: [
    "Reduce next reorder quantity for dermatology products by 20%",
    "Bundle expiring syrup stock into local clinic outreach",
  ],
  generatedAt: "2026-05-09T09:00:00Z",
};

export const fallbackInvestigation: InvestigationResult = {
  question: "Why did profit drop this month?",
  summary:
    "Profit softened because fixed overhead rose while a few chronic-care SKUs sold with lower realized margin, and one upcoming distributor payment is compressing short-term cash.",
  confidence: 0.87,
  evidence: [
    {
      label: "Electricity cost variance",
      detail:
        "Electricity climbed from ₹15.6K to ₹18.2K after cooler-heavy inventory increased.",
      source: "Expense trend",
    },
    {
      label: "Low-turn dermatology stock",
      detail:
        "The current purchase pace implies ₹21K of overstock if demand stays flat.",
      source: "Inventory aging model",
    },
    {
      label: "Upcoming supplier payment",
      detail: "₹53.8K is due before the next high-traffic weekend cycle.",
      source: "Recurring obligations ledger",
    },
  ],
  risks: [
    "Margin can slip further if slow-moving stock is not rebalanced",
    "Cash buffer narrows if recurring bills and supplier payments land together",
  ],
  recommendations: [
    "Trim June reorder quantities on slow dermatology SKUs",
    "Prioritize near-expiry stock in the next clinic outreach cycle",
    "Delay one discretionary purchase until after the next payment weekend",
  ],
  provider: "ollama-local",
  mode: "local-open",
  latencyMs: 180,
  estimatedCostUsd: 0,
};

export const fallbackDocuments: BusinessDocument[] = [
  {
    id: "doc-1",
    title: "May distributor invoice",
    kind: "invoice",
    summary:
      "Primary supplier invoice with chronic-care SKU restock and cold-chain charge.",
    uploadedAt: "2026-05-02",
  },
  {
    id: "doc-2",
    title: "Electricity bill - April cycle",
    kind: "utility",
    summary: "Higher cooler usage due to vaccine inventory and summer demand.",
    uploadedAt: "2026-05-05",
  },
];

export const fallbackActionCenter: ActionCenterSnapshot = {
  headline:
    "Focus first on obligations that can tighten cash, then use the imported ledgers to validate what changed most recently.",
  items: [
    {
      id: "draft-supplier",
      title: "Stage supplier follow-up for Primary distributor payment",
      detail:
        "₹53,800 is due on 2026-05-16. Prepare a message before the next payment cycle tightens cash.",
      severity: "critical",
      actionType: "vendor_follow_up",
      targetEntity: "Primary distributor payment",
      status: "open",
    },
    {
      id: "obligation-rent",
      title: "Protect cash for Shop rent",
      detail:
        "₹55,000 is due in 2 days and should stay visible in the owner plan.",
      severity: "warning",
      actionType: "bill_review",
      targetEntity: "Shop rent",
      status: "open",
    },
  ],
};

export const fallbackImportLedger: ImportLedgerSnapshot = {
  history: [],
  collections: [
    {
      importType: "sales",
      rowCount: 0,
      latestImportAt: null,
      columns: [],
      sampleRows: [],
    },
    {
      importType: "purchases",
      rowCount: 0,
      latestImportAt: null,
      columns: [],
      sampleRows: [],
    },
    {
      importType: "products",
      rowCount: 0,
      latestImportAt: null,
      columns: [],
      sampleRows: [],
    },
    {
      importType: "expenses",
      rowCount: 0,
      latestImportAt: null,
      columns: [],
      sampleRows: [],
    },
    {
      importType: "recurring_obligations",
      rowCount: 0,
      latestImportAt: null,
      columns: [],
      sampleRows: [],
    },
  ],
};
