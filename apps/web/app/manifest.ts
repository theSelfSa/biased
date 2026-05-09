import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "B.I.A.S.E.D.",
    short_name: "BIASED",
    description: "Decision intelligence for smaller businesses.",
    start_url: "/",
    display: "standalone",
    background_color: "#06101b",
    theme_color: "#0891b2",
    icons: [
      {
        src: "/favicon.ico",
        sizes: "48x48",
        type: "image/x-icon",
      },
    ],
  };
}
