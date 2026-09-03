import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During `npm run dev` the API is proxied to a locally running backend.
// In the container build the app is static and nginx proxies /api.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
