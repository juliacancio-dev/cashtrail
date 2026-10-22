import { chromium } from "playwright";
import path from "node:path";
import fs from "node:fs";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `m10-${Date.now()}@example.com`;
const password = "supersecret1";
const log = (...a) => console.log(...a);
const fail = (m) => { console.log("FALHA:", m); process.exitCode = 1; };
const check = (ok, good, bad) => (ok ? log("OK  " + good) : fail(bad));

async function api(method, p, body, token) {
  const res = await fetch(API + p, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${p} -> ${res.status} ${await res.text()}`);
  return res.status === 204 ? null : res.json();
}

await api("POST", "/auth/register", { email, password });
const { access_token: t } = await api("POST", "/auth/login", { email, password });
const acc = await api("POST", "/accounts", { name: "Corrente", type: "checking" }, t);
const sal = await api("POST", "/categories", { name: "Salario" }, t);
const alu = await api("POST", "/categories", { name: "Aluguel" }, t);
const mer = await api("POST", "/categories", { name: "Mercado" }, t);
const tx = (type, amount, description, category, occurred_at) =>
  api("POST", "/transactions", { account_id: acc.id, category_id: category.id, type, amount, description, occurred_at }, t);
await tx("income", "5000.00", "Salario outubro", sal, "2026-10-02");
await tx("expense", "1500.00", "Aluguel outubro", alu, "2026-10-05");
await tx("expense", "200.00", "Feira", mer, "2026-10-06");
await api("POST", "/commitments", { direction: "payable", description: "Aluguel novembro", amount: "800.00", due_date: "2026-10-25", category_id: alu.id }, t);
await api("POST", "/commitments", { direction: "receivable", description: "Freela", amount: "300.00", due_date: "2026-11-10", category_id: sal.id }, t);

const browser = await chromium.launch();
const ctx = await browser.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 1000 } });
const page = await ctx.newPage();
const problems = [];
page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error" && !/404/.test(m.text())) problems.push("console: " + m.text()); });
const shot = (n) => page.screenshot({ path: path.join(OUT, n + ".png"), fullPage: true });

try {
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/accounts");

  // 1. saldo inicial
  await page.getByRole("button", { name: "Editar saldo inicial" }).click();
  await page.locator(`#opening-${acc.id}`).fill("1000");
  await page.getByRole("button", { name: "Salvar" }).click();
  await page.waitForSelector("text=Saldo inicial R$ 1.000,00", { timeout: 5000 }).catch(() => {}); await page.waitForTimeout(800);
  const body1 = await page.locator("main").innerText();
  check(/4\.300,00/.test(body1), "saldo atual da conta = R$ 4.300,00", "saldo atual não é 4.300,00: " + body1.slice(0, 300));
  await shot("m10-1-contas");

  // 2. grupos de DRE
  await page.goto(WEB + "/categories");
  for (const [name, label] of [["Salario", "Receitas"], ["Aluguel", "Despesas fixas"]]) {
    await page.getByRole("combobox", { name: `Grupo no DRE de ${name}` }).click();
    await page.getByRole("option", { name: label, exact: true }).click();
    await page.waitForTimeout(500);
  }
  const cats = await api("GET", "/categories", null, t);
  check(cats.find((c) => c.name === "Salario")?.dre_group === "revenue" && cats.find((c) => c.name === "Aluguel")?.dre_group === "fixed_expense",
    "grupos de DRE gravados pela UI", "grupos não gravados: " + JSON.stringify(cats.map((c) => [c.name, c.dre_group])));
  await shot("m10-2-categorias");

  // 3. DRE
  await page.goto(WEB + "/dre");
  await page.fill("#dre-start", "2026-10-01");
  await page.fill("#dre-end", "2026-10-31");
  await page.waitForSelector("text=sem grupo");
  const dre = await page.locator("main").innerText();
  check(/5\.000,00/.test(dre) && /1\.500,00/.test(dre), "DRE mostra receita 5.000 e despesa fixa 1.500", "DRE sem valores esperados: " + dre.slice(0, 500));
  check(/1 categoria\(s\)/.test(dre), "aviso de categoria sem grupo (Mercado)", "sem aviso de categoria sem grupo");
  await shot("m10-3-dre");
  const dl = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar CSV" }).click();
  const file = await dl.value ?? await dl;
  const p1 = await file.path();
  const csv = fs.readFileSync(p1);
  check(csv[0] === 0xef && csv.toString("utf8").includes(";"), `CSV do DRE baixado (${file.suggestedFilename()})`, "CSV do DRE inválido");

  // 4. Fluxo de caixa
  await page.goto(WEB + "/cash-flow");
  await page.waitForSelector("text=Saldo final projetado");
  const cf = await page.locator("main").innerText();
  check(/4\.300,00/.test(cf), "caixa hoje R$ 4.300,00", "caixa hoje errado: " + cf.slice(0, 400));
  check(/3\.500,00/.test(cf), "saldo projetado out = R$ 3.500,00 (4.300 − 800)", "projetado de outubro não é 3.500,00");
  check(/3\.800,00/.test(cf), "saldo projetado nov = R$ 3.800,00 (+300)", "projetado de novembro não é 3.800,00");
  await page.getByRole("button", { name: "Ver itens: Saídas previstas de out/2026" }).click();
  await page.waitForSelector("text=Aluguel novembro");
  log("OK  drill-down lista 'Aluguel novembro'");
  await shot("m10-4-fluxo");
  const dl2 = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar CSV" }).click();
  const f2 = await dl2;
  check(fs.readFileSync(await f2.path())[0] === 0xef, `CSV do fluxo baixado (${f2.suggestedFilename()})`, "CSV do fluxo inválido");
} catch (e) {
  fail(String(e));
  await shot("m10-erro").catch(() => {});
}
if (problems.length) { log("PROBLEMAS DE CONSOLE:"); problems.forEach((p) => log(" -", p)); }
await browser.close();
