import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import ts from "typescript";
import { routeRoles } from "./routeRoles";
import { navConfig } from "./navConfig";

const SRC = resolve(process.cwd(), "src");

// Routes with no role: public pages and the structural wildcards. Each may
// only carry the listed root element, so an exempt path cannot hide a page.
const EXEMPT: Record<string, string[]> = {
  "/login": ["LoginPage"],
  "/activation/:token": ["ActivationPage"],
  "*": ["RequireAuth", "ForcedPasswordGate", "SessionActivityProvider"],
  "/*": ["Navigate"],
};
const FORBIDDEN_ROUTER_APIS = [
  "useRoutes",
  "createBrowserRouter",
  "createMemoryRouter",
  "createHashRouter",
  "createRoutesFromElements",
];

function parse(text: string, name = "x.tsx") {
  return ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
}

function visit(node: ts.Node, fn: (n: ts.Node) => void) {
  fn(node);
  ts.forEachChild(node, (c) => visit(c, fn));
}

function attr(el: ts.JsxOpeningLikeElement, name: string) {
  return el.attributes.properties.find(
    (a): a is ts.JsxAttribute => ts.isJsxAttribute(a) && a.name.getText() === name
  );
}

/** Rootmost JSX tag of an `element` attribute value, or "" when it is not JSX. */
function rootTag(expr: ts.Expression): string {
  let e: ts.Expression = expr;
  while (ts.isParenthesizedExpression(e)) e = e.expression;
  if (ts.isJsxSelfClosingElement(e)) return e.tagName.getText();
  if (ts.isJsxElement(e)) return e.openingElement.tagName.getText();
  return "";
}

/** Every rule a `<Route>` element in `text` breaks (empty when it is fine). */
function routeViolations(text: string): string[] {
  const out: string[] = [];
  visit(parse(text), (n) => {
    // A renamed or namespaced router import would let a <Route> hide under another tag name.
    if (ts.isImportDeclaration(n) && ts.isStringLiteral(n.moduleSpecifier)) {
      if (/^react-router(-dom)?$/.test(n.moduleSpecifier.text)) {
        const b = n.importClause?.namedBindings;
        if (b && ts.isNamespaceImport(b)) out.push(`Namespace import of ${n.moduleSpecifier.text}`);
        if (b && ts.isNamedImports(b))
          b.elements
            .filter((e) => e.propertyName && e.propertyName.text === "Route")
            .forEach((e) => out.push(`Route is renamed to ${e.name.text}`));
      }
      return;
    }
    if (!ts.isJsxSelfClosingElement(n) && !ts.isJsxOpeningElement(n)) return;
    if (n.tagName.getText() !== "Route") return;
    const pathAttr = attr(n, "path");
    const init = pathAttr?.initializer;
    if (!init || !ts.isStringLiteral(init)) {
      out.push(`Route without a string-literal path: ${n.getText()}`);
      return;
    }
    const path = init.text;
    const elAttr = attr(n, "element");
    const elExpr =
      elAttr?.initializer && ts.isJsxExpression(elAttr.initializer)
        ? elAttr.initializer.expression
        : undefined;
    if (path in EXEMPT) {
      if (!elExpr || !EXEMPT[path].includes(rootTag(elExpr)))
        out.push(`Exempt route ${path} carries an unexpected element`);
      return;
    }
    if (!(path in routeRoles)) out.push(`Route ${path} has no entry in routeRoles`);
    const ok =
      !!elExpr &&
      ts.isCallExpression(elExpr) &&
      elExpr.expression.getText() === "guarded" &&
      elExpr.arguments.length === 2 &&
      ts.isStringLiteral(elExpr.arguments[0]) &&
      elExpr.arguments[0].text === path;
    if (!ok) out.push(`Route ${path} is not wrapped by guarded("${path}", ...)`);
  });
  return out;
}

function routerApiUses(text: string): string[] {
  const out: string[] = [];
  visit(parse(text, "x.ts"), (n) => {
    if (ts.isIdentifier(n) && FORBIDDEN_ROUTER_APIS.includes(n.text)) out.push(n.text);
  });
  return out;
}

function productionFiles(dir: string): string[] {
  return readdirSync(dir, { recursive: true, encoding: "utf8" })
    .filter((f) => /\.tsx?$/.test(f) && !/\.test\.tsx?$/.test(f) && !f.endsWith(".d.ts"))
    .map((f) => join(dir, f));
}

const files = productionFiles(SRC).map((f) => ({ f, text: readFileSync(f, "utf8") }));

describe("route role table (TASK-142, PRB-014)", () => {
  // AC 3: no <Route> anywhere in src is unguarded or undeclared.
  it("scans the production sources (guards the scanner itself)", () => {
    expect(files.length).toBeGreaterThan(50);
    const routeCount = files.reduce((n, { text }) => n + (text.match(/<Route\b/g)?.length ?? 0), 0);
    expect(routeCount).toBeGreaterThanOrEqual(12);
  });

  it.each(files)("every <Route> in $f is declared and guarded", ({ text }) => {
    expect(routeViolations(text)).toEqual([]);
  });

  // AC 3: other ways to declare routes would bypass the scan.
  it("uses no route API other than JSX <Route>", () => {
    const hits = files.flatMap(({ f, text }) => routerApiUses(text).map((u) => `${f}: ${u}`));
    expect(hits).toEqual([]);
  });

  // AC 3: no dead entry in the table.
  it("every table entry has a guarded route in App.tsx", () => {
    const app = files.find((x) => x.f.endsWith("app/App.tsx"))!.text;
    Object.keys(routeRoles).forEach((p) => expect(app).toMatch(new RegExp(`guarded\\(\\s*"${p}"`)));
  });

  // AC 3: guard and navigation share one table.
  it("every nav entry uses the roles of the table", () => {
    navConfig.forEach((e) => {
      expect(Object.keys(routeRoles)).toContain(e.path);
      expect(e.roles).toEqual([...routeRoles[e.path as keyof typeof routeRoles]]);
    });
  });

  it("every role list is non-empty", () => {
    Object.values(routeRoles).forEach((r) => expect(r.length).toBeGreaterThan(0));
  });
});

// Fixtures: the scanner must catch every shape QA found, and accept a good route.
describe("route scanner fixtures (negative controls)", () => {
  it("accepts a guarded route with the attributes in either order", () => {
    expect(
      routeViolations(`<Route path="/consent" element={guarded("/consent", <A />)} />`)
    ).toEqual([]);
    expect(
      routeViolations(`<Route element={guarded("/consent", <A />)} path="/consent" />`)
    ).toEqual([]);
  });

  it("flags an unguarded route", () => {
    expect(routeViolations(`<Route path="/consent" element={<A />} />`)).toHaveLength(1);
  });

  it("flags an element-first unguarded route", () => {
    expect(
      routeViolations(`<Route element={<ConsentPage />} path="/secret" />`).length
    ).toBeGreaterThan(0);
  });

  it("flags an expression path", () => {
    expect(routeViolations(`<Route path={"/secret"} element={<AccountsPage />} />`)).toHaveLength(
      1
    );
    expect(routeViolations(`<Route path={p} element={guarded(p, <A />)} />`)).toHaveLength(1);
  });

  it("flags a route without a path", () => {
    expect(routeViolations(`<Route index element={<A />} />`)).toHaveLength(1);
  });

  it("flags a guard for a different path", () => {
    expect(
      routeViolations(`<Route path="/consent" element={guarded("/profile", <A />)} />`)
    ).toHaveLength(1);
  });

  it("flags a path missing from the table, even if guarded", () => {
    expect(routeViolations(`<Route path="/new" element={guarded("/new", <A />)} />`)).toHaveLength(
      1
    );
  });

  it("flags a page hidden behind an exempt path", () => {
    expect(routeViolations(`<Route path="*" element={<AccountsPage />} />`)).toHaveLength(1);
    expect(routeViolations(`<Route path="/*" element={<AccountsPage />} />`)).toHaveLength(1);
  });

  it("flags a renamed Route import (QA probe R2-3)", () => {
    const src = `import { Route as R } from "react-router-dom";\n<R path="/alias" element={<A />} />`;
    expect(routeViolations(src).length).toBeGreaterThan(0);
  });

  it("flags a namespace import of the router (QA probe R2-3)", () => {
    const src = `import * as RR from "react-router-dom";\n<RR.Route path="/ns" element={<A />} />`;
    expect(routeViolations(src).length).toBeGreaterThan(0);
  });

  it("accepts the plain Route import", () => {
    expect(routeViolations(`import { Route, Routes } from "react-router-dom";`)).toEqual([]);
  });

  it("flags router APIs that declare routes without <Route>", () => {
    expect(routerApiUses(`const r = useRoutes([]);`)).toEqual(["useRoutes"]);
    expect(routerApiUses(`createBrowserRouter([]); createRoutesFromElements(x);`)).toEqual([
      "createBrowserRouter",
      "createRoutesFromElements",
    ]);
  });
});
