import { describe, expect, it } from "vitest";
import fs from "fs";
import path from "path";
import ts from "typescript";

// Saathi rule: every visible word is bilingual. Text must go through <Bi hi=… en=…> (or both()/pick()),
// never as a bare English JSX literal or a one-language attribute.
function files(dir: string, out: string[] = []): string[] {
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f);
    if (fs.statSync(p).isDirectory()) files(p, out);
    else if (p.endsWith(".tsx")) out.push(p);
  }
  return out;
}

const LATIN = /[A-Za-z]{2,}/;
// Design-intended tokens that are the same in both languages: the language switch and the demo badge.
const SAME_IN_BOTH = new Set(["EN", "DEMO"]);
const ONE_LANG_ATTRS = new Set(["placeholder", "aria-label", "title", "alt"]);

describe("bilingual text", () => {
  it("has no bare English JSX text and no English-only labelling attributes", () => {
    const problems: string[] = [];
    for (const file of [...files(path.join(process.cwd(), "src/app")), ...files(path.join(process.cwd(), "src/components"))]) {
      const src = ts.createSourceFile(file, fs.readFileSync(file, "utf-8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
      const visit = (node: ts.Node) => {
        if (ts.isJsxText(node) && LATIN.test(node.text.trim()) && !SAME_IN_BOTH.has(node.text.trim())) problems.push(`${path.relative(process.cwd(), file)}: text "${node.text.trim()}"`);
        if (ts.isJsxAttribute(node) && ONE_LANG_ATTRS.has(node.name.getText()) && node.initializer && ts.isStringLiteral(node.initializer)) {
          const v = node.initializer.text;
          if (LATIN.test(v) && !/[ऀ-ॿ]/.test(v)) problems.push(`${path.relative(process.cwd(), file)}: ${node.name.getText()}="${v}"`);
        }
        ts.forEachChild(node, visit);
      };
      visit(src);
    }
    expect(problems).toEqual([]);
  });
});
