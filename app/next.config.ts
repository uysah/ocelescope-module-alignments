import type { NextConfig } from "next";

const apiBase = process.env.EXTERNAL_API_BASE_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
	reactStrictMode: true,
	transpilePackages: [
		"@mantine/charts",
		"recharts",
		"@instance/example-module",
		 "@r4pm/components",
		 
	],
	rewrites: async () => [
		{ source: "/api/external/:path*", destination: `${apiBase}/:path*` },
	],
};

export default nextConfig;
