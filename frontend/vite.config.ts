import { relative } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
    {
      // Lists the source modules inside each chunk, next to the manifest, so
      // scripts/check-bundle-budget.mjs can see page code that Rollup merged into the entry chunk
      // (SR-026 AC 7). Removed from dist with the manifest after the check.
      name: "chunk-modules",
      generateBundle(_options, bundle) {
        const modules: Record<string, string[]> = {};
        for (const [file, chunk] of Object.entries(bundle)) {
          if (chunk.type === "chunk") {
            modules[file] = Object.keys(chunk.modules).map((id) =>
              relative(process.cwd(), id.split("?")[0]).split("\\").join("/")
            );
          }
        }
        this.emitFile({
          type: "asset",
          fileName: ".vite/chunk-modules.json",
          source: JSON.stringify(modules),
        });
      },
    },
  ],
  // The manifest lets scripts/check-bundle-budget.mjs find the initial chunks (SR-026 AC 7).
  build: { manifest: true },
});
