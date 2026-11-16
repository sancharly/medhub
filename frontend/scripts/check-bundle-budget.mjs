// Initial-payload budget check (SR-026 AC 7, TASK-145; TS-018 TC-018.10).
//
// The initial JavaScript is the entry chunk plus every chunk it imports statically, taken from the
// Vite manifest (`build.manifest`). Lazy route chunks are not part of it. It is measured in gzip
// bytes (zlib default level, as the Vite build report does), 1 kB = 1000 bytes.
//
// A page made eager is merged into the entry chunk by Rollup, so it never shows up as a lazy chunk in
// the graph. The check therefore requires each expected lazy group to be a chunk of its own.
//
// Usage: node scripts/check-bundle-budget.mjs [distDir] [--clean]   (run after `vite build`)
// --clean removes dist/.vite (the manifest) once the check passed, so it is not published.
import { readFileSync, rmSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

/** SR-026 AC 7 (approved: CR-006 D-8, Plan gate P-2): at most 165 kB gzip. */
export const BUDGET_GZIP_BYTES = 165 * 1000;

/** Source prefix of a lazy group: its directory, or the page file itself. */
const sourcePrefix = (key) => (key.endsWith("/index.ts") ? key.slice(0, -"index.ts".length) : key);

/** Manifest keys of the lazy route groups (TASK-145): each must be its own dynamic-entry chunk. */
export const LAZY_GROUPS = [
  "src/auth/ChangePasswordPage.tsx",
  "src/core/patients/index.ts",
  "src/core/clinical/index.ts",
  "src/core/appointments/index.ts",
  "src/core/consent/index.ts",
  "src/core/admin/index.ts",
];

const kB = (bytes) => (bytes / 1000).toFixed(2);

export function measureInitial(distDir) {
  const manifest = JSON.parse(readFileSync(join(distDir, ".vite", "manifest.json"), "utf8"));
  const entryKey = Object.keys(manifest).find((k) => manifest[k].isEntry);
  if (!entryKey) throw new Error("no entry chunk in the manifest");

  const seen = new Set();
  const visit = (key) => {
    if (seen.has(key)) return;
    seen.add(key);
    for (const next of manifest[key].imports ?? []) visit(next);
  };
  visit(entryKey);

  const modules = JSON.parse(readFileSync(join(distDir, ".vite", "chunk-modules.json"), "utf8"));

  const files = [...seen].map((key) => {
    const code = readFileSync(join(distDir, manifest[key].file));
    const file = manifest[key].file;
    return {
      key,
      file,
      raw: code.length,
      gzip: gzipSync(code).length,
      modules: modules[file] ?? [],
    };
  });
  return {
    manifest,
    files,
    totalGzip: files.reduce((n, f) => n + f.gzip, 0),
    totalRaw: files.reduce((n, f) => n + f.raw, 0),
  };
}

export function checkBudget(distDir, budgetBytes = BUDGET_GZIP_BYTES) {
  const r = measureInitial(distDir);
  const lines = r.files.map((f) => `  ${f.file}  ${kB(f.raw)} kB raw, ${kB(f.gzip)} kB gzip`);
  const summary = `initial JavaScript ${kB(r.totalGzip)} kB gzip (${kB(r.totalRaw)} kB raw), budget ${kB(budgetBytes)} kB gzip`;

  // A lazy chunk in the static graph means a lazy page was imported eagerly somewhere.
  const lazyInGraph = r.files.filter((f) => r.manifest[f.key].isDynamicEntry);
  if (lazyInGraph.length > 0) {
    const names = lazyInGraph.map((f) => f.key).join(", ");
    return {
      ...r,
      ok: false,
      message: `${summary}\n${lines.join("\n")}\nlazy chunk in the initial graph: ${names}`,
    };
  }
  const inInitial = new Set(r.files.map((f) => f.file));
  const notSplit = LAZY_GROUPS.filter((key) => {
    const entry = r.manifest[key];
    return !entry || !entry.isDynamicEntry || inInitial.has(entry.file);
  });
  // Rollup keeps a tiny re-export chunk for an eagerly imported page, so also look for the page's own
  // modules inside the initial chunks.
  const prefixes = LAZY_GROUPS.map(sourcePrefix);
  const merged = LAZY_GROUPS.filter((key, i) =>
    r.files.some((f) => f.modules.some((m) => m.startsWith(prefixes[i])))
  );
  for (const key of merged) if (!notSplit.includes(key)) notSplit.push(key);
  if (notSplit.length > 0) {
    return {
      ...r,
      ok: false,
      message: `${summary}\n${lines.join("\n")}\nnot a lazy chunk of its own (imported eagerly?): ${notSplit.join(", ")}`,
    };
  }
  if (r.totalGzip > budgetBytes) {
    return { ...r, ok: false, message: `${summary}: exceeds the budget\n${lines.join("\n")}` };
  }
  return { ...r, ok: true, message: `${summary}: within the budget\n${lines.join("\n")}` };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const dist = resolve(
    args.find((a) => !a.startsWith("--")) ??
      join(dirname(fileURLToPath(import.meta.url)), "..", "dist")
  );
  const result = checkBudget(dist);
  console.log(result.message);
  if (result.ok && args.includes("--clean"))
    rmSync(join(dist, ".vite"), { recursive: true, force: true });
  process.exit(result.ok ? 0 : 1);
}
