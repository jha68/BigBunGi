import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          markdown: ["react-markdown", "remark-gfm"],
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
