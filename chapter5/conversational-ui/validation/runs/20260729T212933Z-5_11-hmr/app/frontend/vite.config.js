import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite 开发服务器默认开启 HMR（热模块替换）。
// 当 Agent 修改 src/ 下的源码时，浏览器无需整页刷新即可即时看到界面变化。
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 后端 FastAPI 跑在 8000，前端把 /api 请求代理过去，避免跨域。
    proxy: {
      "/api": "http://127.0.0.1:56044",
    },
  },
});
