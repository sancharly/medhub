import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/tests/setup.ts"],
    environmentOptions: {
      jsdom: {
        url: "http://localhost",
      },
    },
    coverage: {
      provider: "v8",
    },
    server: {
      deps: {
        inline: [/@mui/, /react-transition-group/],
      },
    },
  },
});
