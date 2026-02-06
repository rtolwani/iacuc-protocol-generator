import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Output standalone for deployment (Render, Railway, Docker)
  output: "standalone",
  
  // Allow images from any domain (for future use)
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
