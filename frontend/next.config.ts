import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Output standalone for deployment (Render, Railway, Docker)
  output: "standalone",
  
  // Disable image optimization for simpler deployment
  images: {
    unoptimized: true,
  },
  
  // Skip ESLint during build
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Skip TypeScript errors during build
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
