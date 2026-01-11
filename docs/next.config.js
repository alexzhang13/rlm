/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/rlm',
  trailingSlash: true,
  images: { unoptimized: true },
};

module.exports = nextConfig;

