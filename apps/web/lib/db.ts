import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";

import { appEnv } from "@/lib/env";

const globalForDb = globalThis as typeof globalThis & {
  biasedPool?: Pool;
};

export const pool =
  globalForDb.biasedPool ??
  new Pool({
    connectionString: appEnv.databaseUrl,
  });

if (process.env.NODE_ENV !== "production") {
  globalForDb.biasedPool = pool;
}

export const db = drizzle(pool);
