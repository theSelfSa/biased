import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@biased/contracts", "@biased/ui"],
  serverExternalPackages: ["pg"],
};

export default nextConfig;
