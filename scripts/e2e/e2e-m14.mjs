import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `m14-${Date.now()}@example.com`;
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
const cc = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "100000" }, t);
const corretora = await api("POST", "/accounts", { name: "Corretora", type: "investment" }, t);
const saude = await api("POST", "/categories", { name: "Plano de saude" }, t);
const gain = await api("POST", "/categories", { name: "Ganho de capital", dre_group: "financial_revenue" }, t);
await api("POST", "/transactions", {
  account_id: cc.id, category_id: saude.id, type: "expense", amount: "4000", occurred_at: "2026-05-10", description: "Plano",
}, t);
const petr = await api("POST", "/investments/assets", {
  account_id: corretora.id, name: "Petrobras PN", symbol: "PETR4", asset_class: "stock", quote_source: "manual",
}, t);
await api("POST", `/investments/assets/${petr.id}/operations`, {
  kind: "buy", occurred_at: "2026-02-02", quantity: "1000", unit_price: "20", cash_account_id: cc.id,
}, t);
await api("POST", `/investments/assets/${petr.id}/operations`, {
  kind: "sell", occurred_at: "2026-03-10", quantity: "1000", unit_price: "30", cash_account_id: cc.id, category_id: gain.id,
}, t);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 1500 } });
const problems = [];
page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error" && !/404|401/.test(m.text())) problems.push("console: " + m.text()); });
const shot = (n) => page.screenshot({ path: path.join(OUT, n + ".png"), fullPage: true });

try {
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/accounts");

  // marca fiscal pela tela
  await page.goto(WEB + "/categories");
  await page.getByRole("combobox", { name: "Marca fiscal de Plano de saude" }).click();
  await page.getByRole("option", { name: "Saúde (dedutível)" }).click();
  await page.waitForTimeout(600);
  const cats = await api("GET", "/categories", null, t);
  check(cats.find((c) => c.name === "Plano de saude").ir_kind === "deduction_health", "marca fiscal de saúde gravada pela tela", "marca não gravada");

  // informe pela tela
  await page.goto(WEB + "/tax");
  await page.waitForSelector("text=Informes de rendimentos");
  await page.locator("#st-payer").fill("Empresa X");
  await page.locator("#st-gross").fill("100000");
  await page.locator("#st-inss").fill("8000");
  await page.locator("#st-irrf").fill("12000");
  await page.getByRole("button", { name: "Adicionar informe" }).click();
  await page.waitForSelector("text=Empresa X · bruto");
  log("OK  informe cadastrado pela tela");

  await page.waitForSelector("text=mais vantajosa");
  const text = (await page.locator("main").innerText()).replace(/\n/g, " ");
  check(/Imposto devido\s*R\$\s11\.744,34/.test(text), "simplificada: imposto devido R$ 11.744,34 (conferido à mão)", "imposto simplificado não bate: " + text.slice(0, 700));
  check(/A restituir\s*R\$\s255,66/.test(text), "a restituir R$ 255,66 com IRRF de R$ 12.000", "saldo a restituir não bate");
  check(/DARF/.test(text) && /1\.498,50/.test(text.replace(/\s/g, " ")), "DARF de março: R$ 1.498,50", "DARF não aparece");
  check(/Parâmetros consultados em/.test(text) && /Premissas não verificadas/.test(text), "fontes e premissas não verificadas aparecem", "sem fontes/premissas");
  await shot("m14-1-irpf");

  const dl = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar CSV" }).click();
  const file = await dl;
  check(file.suggestedFilename() === "irpf-2026.csv", "CSV do dossiê baixado", "CSV não baixou");
} catch (e) {
  fail(String(e).slice(0, 700));
  await shot("m14-erro").catch(() => {});
}
if (problems.length) { log("PROBLEMAS DE CONSOLE:"); problems.forEach((p) => log(" -", p)); }
await browser.close();
