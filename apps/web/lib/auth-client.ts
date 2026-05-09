import { createAuthClient } from "better-auth/react";

import { appEnv } from "@/lib/env";

export const authClient = createAuthClient({
  baseURL: appEnv.appUrl,
});
