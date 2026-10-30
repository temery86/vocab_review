// Phase 2 checks on the demo build (fictional data). Every screen at phone and desktop width in light and dark,
// an automated accessibility scan (axe, WCAG 2.1 A and AA), no sideways scrolling, and a keyboard only pass through
// sign in and a batch. Writes ../reports/frontend-check-report.md and screenshots in ../reports/screens/.
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

const PORT = 4179, BASE = `http://localhost:${PORT}/?demo`;
const OUT = fileURLToPath(new URL("../../reports/", import.meta.url));
mkdirSync(OUT + "screens", { recursive: true });
const server = spawn("npx", ["vite", "preview", "--port", String(PORT), "--strictPort"], { stdio: "ignore" });
await new Promise((r) => setTimeout(r, 2500));
const results = [], log = (name, ok, detail = "") => { results.push([name, ok, detail]); console.log(ok ? "PASS" : "FAIL", name, detail); };

async function signIn(page, email) {
  await page.goto(BASE);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.fill("#email", email);
  await page.click("#f1 button");
  await page.fill("#code", "123456");
  await page.click("#f2 button");
  await page.waitForSelector("h1:has-text('Your batches')");
}

const browser = await chromium.launch();
const screens = [
  ["sign in", null, async (p) => { await p.goto(BASE); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForSelector("#email"); }],
  ["privacy note", null, async (p) => { await p.goto(BASE + "#/privacy"); await p.waitForSelector("h1"); }],
  ["home", "alice@example.org", async () => {}],
  ["brief", "alice@example.org", async (p) => { await p.goto(BASE + "#/b/b-demo-01"); await p.waitForSelector("#go"); }],
  ["survey item, graded", "alice@example.org", async (p) => { await p.goto(BASE + "#/b/b-demo-01/1"); await p.waitForSelector("#qs fieldset");
    await p.click("[data-q=b][data-v=no]"); await p.waitForSelector(".nb"); }],
  ["register item", "alice@example.org", async (p) => { await p.goto(BASE + "#/b/b-demo-02/1"); await p.waitForSelector("#qs fieldset"); }],
  ["curation placement", "alice@example.org", async (p) => { await p.goto(BASE + "#/b/b-demo-03/1"); await p.waitForSelector("#qs fieldset");
    await p.click("[data-q=b][data-v=reject]"); await p.waitForSelector("#rr"); }],
  ["curation membership", "alice@example.org", async (p) => { await p.goto(BASE + "#/b/b-demo-03/3"); await p.waitForSelector(".members");
    await p.click(".members [data-v=move]"); await p.waitForSelector("[data-t]"); }],
  ["end of batch", "alice@example.org", async (p) => { await p.goto(BASE + "#/b/b-demo-01/end"); await p.waitForSelector("#f"); }],
  ["admin", "owner@example.org", async (p) => { await p.goto(BASE + "#/admin"); await p.waitForSelector("table"); }],
];
for (const [w, h, label] of [[390, 844, "phone"], [1280, 860, "desktop"]]) {
  for (const scheme of ["light", "dark"]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, colorScheme: scheme });
    const page = await ctx.newPage();
    for (const [name, who, go] of screens) {
      if (who) await signIn(page, who);
      await go(page);
      await page.waitForTimeout(150);
      const ax = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
      const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      const v = ax.violations.map((x) => `${x.id} (${x.nodes.length})`).join(", ");
      log(`${name}, ${label}, ${scheme}`, ax.violations.length === 0 && over <= 0, (v || "no axe violations") + (over > 0 ? `, ${over}px sideways scroll` : ""));
      await page.screenshot({ path: `${OUT}screens/${name.replace(/[ ,]+/g, "-")}-${label}-${scheme}.png`, fullPage: true });
    }
    await ctx.close();
  }
}

// Keyboard only
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 } });
  const p = await ctx.newPage();
  await p.goto(BASE); await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.waitForSelector("#email"); await p.focus("#email");
  await p.keyboard.type("alice@example.org"); await p.keyboard.press("Enter");
  await p.waitForSelector("#code:visible"); await p.keyboard.type("123456"); await p.keyboard.press("Enter");
  await p.waitForSelector("h1:has-text('Your batches')");
  let ok = true;
  // Tab to the first Start link and open it
  for (let k = 0; k < 15; k++) { await p.keyboard.press("Tab"); if (await p.evaluate(() => document.activeElement?.textContent?.trim() === "Start")) break; }
  ok &&= await p.evaluate(() => document.activeElement?.textContent?.trim() === "Start");
  await p.keyboard.press("Enter"); await p.waitForSelector("#go");
  await p.keyboard.press("Enter"); await p.waitForSelector("#qs fieldset");
  await p.keyboard.press("y"); await p.waitForTimeout(150);          // question 1 yes
  await p.keyboard.press("n"); await p.waitForTimeout(150);          // question 2 no
  const q2 = await p.evaluate(() => !!document.querySelector("[aria-label='Correct grade']"));
  await p.keyboard.press("Enter"); await p.waitForTimeout(150);      // next item
  const pos2 = await p.evaluate(() => location.hash);
  await p.keyboard.press("n"); await p.waitForTimeout(150); await p.keyboard.press("2"); await p.waitForTimeout(150);   // no, neighbour 2
  const nb = await p.evaluate(() => document.querySelectorAll(".nb .choice.on").length);
  await p.keyboard.press("Backspace"); await p.waitForTimeout(150);
  const back = await p.evaluate(() => location.hash);
  const saved = await p.evaluate(() => JSON.parse(localStorage.getItem("vr-demo-state-v1")).responses.filter((r) => r.assignment_id <= 20).length);
  // focus is visible
  await p.keyboard.press("Tab");
  const ring = await p.evaluate(() => getComputedStyle(document.activeElement).outlineStyle);
  log("keyboard only, sign in, open a batch, answer both questions, pick a neighbour, go back", ok && q2 && pos2.endsWith("/2") && nb === 1 && back.endsWith("/1") && saved >= 4 && ring !== "none",
      `question 2 correct grade shown ${q2}, moved to ${pos2}, neighbour chosen ${nb}, back to ${back}, ${saved} responses saved, focus outline ${ring}`);
  await ctx.close();
}
// Gold fields never reach the reviewer's screen
{
  const ctx = await browser.newContext();
  const p = await ctx.newPage();
  await signIn(p, "alice@example.org");
  await p.goto(BASE + "#/b/b-demo-01/4"); await p.waitForSelector("#qs fieldset");
  const html = await p.content();
  log("gold item looks like any other", !/gold/i.test(html), "the page has no gold field or label");
  await ctx.close();
}
await browser.close();
server.kill();
const L = ["# Front end check report", "", `Run ${new Date().toISOString().slice(0, 16).replace("T", " ")} UTC by \`web/tests/check.mjs\` with headless Chromium (Playwright) on the demo build, which runs on fictional data in the browser. ` +
  "Accessibility by axe-core with the WCAG 2.1 A and AA rules. Sideways scroll is page width beyond the viewport. Screenshots in `screens/`. The manual check of the review screen is in the section below.", "",
  `${results.length} checks, ${results.filter((r) => r[1]).length} passed.`, "", "| Check | Result | Detail |", "|---|---|---|",
  ...results.map(([n, ok, d]) => `| ${n} | ${ok ? "pass" : "FAIL"} | ${String(d).replace(/\|/g, "/")} |`)];
writeFileSync(OUT + "frontend-check-report.md", L.join("\n") + "\n");
process.exit(results.every((r) => r[1]) ? 0 : 1);
