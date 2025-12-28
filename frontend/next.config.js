/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export for S3/CloudFront deployment
  output: 'export',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Generate content-hash filenames for cache-busting
  // (Next.js does this by default in production builds)

  // Enable strict mode for catching potential issues
  reactStrictMode: true,

  // Trailing slashes for S3 static hosting compatibility
  trailingSlash: true,
}

module.exports = nextConfig
