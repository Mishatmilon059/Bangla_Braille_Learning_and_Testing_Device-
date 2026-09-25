import type { NextConfig } from "next";

const isStaticExport = process.env.EXPORT_STATIC === "true";
const basePath = process.env.BASE_PATH || "";

const nextConfig: NextConfig = {
  output: isStaticExport ? "export" : undefined,
  basePath: basePath ? basePath : undefined,
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
};

export default nextConfig;
