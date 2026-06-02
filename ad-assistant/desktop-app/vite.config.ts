import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    watch: {
      // 忽略 Tauri Rust 构建产物目录，避免 EBUSY 冲突
      ignored: ["**/src-tauri/target/**"],
    },
    // Proxy /api → cloud backend so the browser sends same-origin requests
    // (avoids CORS errors during local development).
    // Requires VITE_CLOUD_API_BASE_URL=http://127.0.0.1:5173 at dev-server start.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
