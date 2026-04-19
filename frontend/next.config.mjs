/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiTarget =
      process.env.FRYING_PAN_API_PROXY_TARGET ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "http://localhost:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${apiTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
