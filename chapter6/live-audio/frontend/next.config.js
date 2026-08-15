const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  env: {
    WEBSOCKET_PORT: process.env.WEBSOCKET_PORT || '8848',
    IS_PRODUCTION: process.env.NODE_ENV === 'production',
  },
  // Since we're using static export, we need to disable image optimization
  images: {
    unoptimized: true,
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname),
    };
    return config;
  }
}

module.exports = nextConfig
