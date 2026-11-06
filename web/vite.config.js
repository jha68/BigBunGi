import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const workerVersion = createHash("sha256")
  .update(readFileSync(new URL("./public/python-worker.js", import.meta.url)))
  .update(readFileSync(new URL("./pyodide-manifest.json", import.meta.url)))
  .digest("hex")
  .slice(0, 12);

export default defineConfig({
  base: "./",
  plugins: [react()],
  define: { __PYTHON_WORKER_VERSION__: JSON.stringify(workerVersion) },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          markdown: ["react-markdown", "remark-gfm"],
          math: ["remark-math", "rehype-katex", "katex"],
          editor: [
            "codemirror",
            "@codemirror/lang-python",
            "@codemirror/theme-one-dark",
          ],
        },
      },
    },
  },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
