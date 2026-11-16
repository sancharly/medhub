// @vitest-environment node
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, existsSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { randomBytes } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import {
  BUDGET_GZIP_BYTES,
  LAZY_GROUPS,
  measureInitial,
  checkBudget,
} from "./check-bundle-budget.mjs";

// SR-026 AC 7, TASK-145 (TS-018 TC-018.10): the initial JavaScript is the entry chunk plus its static
// imports, measured in gzip bytes on the production build, at most 165 kB; every lazy route group is
// a chunk of its own.

const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const script = join(frontendRoot, "scripts", "check-bundle-budget.mjs");
const viteBin = join(frontendRoot, "node_modules", "vite", "bin", "vite.js");
const tmpRoots = [];
afterAll(() => tmpRoots.forEach((d) => rmSync(d, { recursive: true, force: true })));

const tmp = (prefix) => {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  tmpRoots.push(dir);
  return dir;
};

/**
 * A fake dist. Random bytes do not compress, so gzip size is close to the byte count given. Every
 * lazy group is a small dynamic-entry chunk unless `manifestPatch` says otherwise.
 */
function fakeDist({
  entry = 40_000,
  vendor = 60_000,
  entryImports = ["_vendor.js"],
  without = [],
  entryModules,
}) {
  const dir = tmp("budget-");
  mkdirSync(join(dir, "assets"), { recursive: true });
  mkdirSync(join(dir, ".vite"), { recursive: true });
  const manifest = {
    "index.html": {
      file: "assets/index.js",
      isEntry: true,
      imports: entryImports,
      dynamicImports: LAZY_GROUPS,
    },
    "_vendor.js": { file: "assets/vendor.js" },
  };
  writeFileSync(join(dir, "assets", "index.js"), randomBytes(entry));
  writeFileSync(join(dir, "assets", "vendor.js"), randomBytes(vendor));
  LAZY_GROUPS.forEach((key, i) => {
    if (without.includes(key)) return;
    manifest[key] = { file: `assets/lazy${i}.js`, isDynamicEntry: true };
    writeFileSync(join(dir, "assets", `lazy${i}.js`), randomBytes(5000));
  });
  writeFileSync(join(dir, ".vite", "manifest.json"), JSON.stringify(manifest));
  const modules = {
    "assets/index.js": ["src/app/App.tsx", ...(entryModules ?? [])],
    "assets/vendor.js": ["node_modules/react/index.js"],
  };
  LAZY_GROUPS.forEach((key, i) => (modules[`assets/lazy${i}.js`] = [key]));
  writeFileSync(join(dir, ".vite", "chunk-modules.json"), JSON.stringify(modules));
  return dir;
}

describe("check-bundle-budget (synthetic output)", () => {
  it("counts the entry chunk and its static imports, not the lazy chunks", () => {
    const dir = fakeDist({});
    const r = measureInitial(dir);
    expect(r.files.map((f) => f.file).sort()).toEqual(["assets/index.js", "assets/vendor.js"]);
    expect(r.totalGzip).toBeGreaterThan(100_000);
    expect(r.totalGzip).toBeLessThan(101_000);
    expect(checkBudget(dir, BUDGET_GZIP_BYTES).ok).toBe(true);
  });

  it("fails when the initial payload is over the budget", () => {
    const r = checkBudget(fakeDist({ entry: 90_000, vendor: 90_000 }), BUDGET_GZIP_BYTES);
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/exceeds/);
  });

  it("fails when a lazy chunk is pulled into the static graph", () => {
    const dir = fakeDist({
      entry: 1000,
      vendor: 1000,
      entryImports: ["_vendor.js", LAZY_GROUPS[1]],
    });
    const r = checkBudget(dir, BUDGET_GZIP_BYTES);
    expect(r.ok).toBe(false);
    expect(r.message).toContain(LAZY_GROUPS[1]);
  });

  it("fails when a lazy group has no chunk of its own (merged into the entry)", () => {
    const r = checkBudget(fakeDist({ without: ["src/core/patients/index.ts"] }), BUDGET_GZIP_BYTES);
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/not a lazy chunk of its own.*src\/core\/patients\/index\.ts/);
  });

  it("fails when a lazy group's code is inside the entry chunk", () => {
    const dir = fakeDist({ entryModules: ["src/core/patients/PatientListPage.tsx"] });
    const r = checkBudget(dir, BUDGET_GZIP_BYTES);
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/not a lazy chunk of its own.*src\/core\/patients\/index\.ts/);
  });

  it("the budget is the approved 165 kB gzip", () => {
    expect(BUDGET_GZIP_BYTES).toBe(165_000);
  });

  it("--clean removes the manifest after a pass and leaves it after a failure", () => {
    const ok = fakeDist({});
    const passed = spawnSync(process.execPath, [script, ok, "--clean"], { encoding: "utf8" });
    expect(passed.status).toBe(0);
    expect(existsSync(join(ok, ".vite"))).toBe(false);

    const bad = fakeDist({ without: ["src/core/patients/index.ts"] });
    const failed = spawnSync(process.execPath, [script, bad, "--clean"], { encoding: "utf8" });
    expect(failed.status).toBe(1);
    expect(existsSync(join(bad, ".vite"))).toBe(true);
  });
});

/** A child process: the test runner sets NODE_ENV=test, which would build the development React. */
function viteBuild(outDir, config) {
  const args = [viteBin, "build", "--outDir", outDir, "--emptyOutDir", "--logLevel", "silent"];
  if (config) args.push("--config", config);
  execFileSync(process.execPath, args, {
    cwd: frontendRoot,
    env: { ...process.env, NODE_ENV: "production" },
    stdio: "pipe",
  });
}

describe("production build", () => {
  const outDir = join(tmpdir(), `medhub-budget-build-${process.pid}`);
  tmpRoots.push(outDir);
  beforeAll(() => viteBuild(outDir), 120_000);

  it("landing route does not import admin pages or any other lazy page", () => {
    const r = measureInitial(outDir);
    const inInitial = new Set(r.files.map((f) => f.file));
    for (const src of LAZY_GROUPS) {
      const entry = r.manifest[src];
      expect(entry, `${src} has its own chunk`).toBeDefined();
      expect(entry.isDynamicEntry, `${src} is a dynamic entry`).toBe(true);
      expect(inInitial.has(entry.file), `${src} is not in the initial graph`).toBe(false);
    }
  });

  it("admin pages share one chunk", () => {
    const r = measureInitial(outDir);
    expect(r.manifest["src/core/admin/index.ts"].file).toMatch(/assets\//);
    expect(r.manifest["src/core/admin/accounts/index.ts"]).toBeUndefined();
  });

  it("initial JavaScript is within 165 kB gzip", () => {
    const r = checkBudget(outDir, BUDGET_GZIP_BYTES);
    expect(r.message).toMatch(/kB gzip/);
    expect(r.ok, r.message).toBe(true);
  });

  // Negative control on a real build: a static import of a lazy page's module makes Rollup merge it
  // into the entry chunk, which the initial-graph test cannot see and the budget may not catch.
  it("a lazy page imported eagerly fails the check", () => {
    const dir = tmp("eager-");
    const cfg = join(dir, "vite.eager.config.mts");
    writeFileSync(
      cfg,
      `import base from ${JSON.stringify(join(frontendRoot, "vite.config.ts"))};
export default {
  ...base,
  plugins: [
    ...base.plugins,
    {
      name: "make-patients-eager",
      transform(code, id) {
        if (id.endsWith("/app/App.tsx")) return (
          'import { PatientListPage as Eager } from "../core/patients/index";\\n' +
          code +
          "\\nglobalThis.eager = Eager;\\n"
        );
      },
    },
  ],
};
`
    );
    const out = join(dir, "dist");
    viteBuild(out, cfg);
    const r = checkBudget(out, BUDGET_GZIP_BYTES);
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/not a lazy chunk of its own.*src\/core\/patients\/index\.ts/);
  }, 120_000);
});

// PRB-093 (CR-007 D-1): run on its own after `npm run build`, which removes the manifest, the check
// gives a verdict (message and exit 1) instead of an uncaught ENOENT stack trace. Never a pass.
describe("budget check without a manifest (TC-018.10, PRB-093)", () => {
  const run = (dir, ...extra) =>
    spawnSync(process.execPath, [script, dir, ...extra], { encoding: "utf8" });

  it("a missing manifest gives a clear message and exit 1", () => {
    const dir = tmp("nomanifest-");
    const r = run(dir);
    expect(r.status).toBe(1);
    expect(r.stderr).toContain("manifest.json");
    expect(r.stderr).toContain("npm run build");
    for (const out of [r.stdout, r.stderr]) {
      expect(out).not.toContain("within the budget");
      expect(out).not.toContain("ENOENT");
      expect(out).not.toContain("    at ");
    }
  });

  it("a missing manifest with --clean removes nothing", () => {
    const dir = tmp("nomanifest-clean-");
    mkdirSync(join(dir, "assets"));
    writeFileSync(join(dir, "assets", "a.js"), "x");
    const r = run(dir, "--clean");
    expect(r.status).toBe(1);
    expect(existsSync(join(dir, "assets", "a.js"))).toBe(true);
    expect(readdirSync(dir)).toEqual(["assets"]);
  });
});
