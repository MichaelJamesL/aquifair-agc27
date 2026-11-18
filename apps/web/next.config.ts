import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Cache Components and partial prefetching are off: every screen is static demo data, and the
  // workspace layout reads the URL on the client, which would need extra Suspense boundaries.
  // the floating dev badge sits on top of the layers panel footnote
  devIndicators: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
