import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `m13-${Date.now()}@example.com`;
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
const iso = (d) => d.toISOString().slice(0, 10);
const today = new Date();
const start = new Date(today.getTime() - 20 * 86400000);

await api("POST", "/auth/register", { email, password });
const { access_token: t } = await api("POST", "/auth/login", { email, password });
await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "10000" }, t);
await api("POST", "/accounts", { name: "Corretora", type: "investment" }, t);
await api("POST", "/categories", { name: "Ganho de capital", dre_group: "financial_revenue" }, t);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 1300 } });
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

  await page.goto(WEB + "/investments");
  await page.getByRole("button", { name: "Novo ativo" }).click();
  const form = page.getByRole("form", { name: "Novo ativo" });
  await form.locator("#inv-name").fill("Petrobras PN");
  await form.locator("#inv-symbol").fill("petr4");
  await form.getByRole("button", { name: "Cadastrar ativo" }).click();
  await page.waitForSelector("text=Petrobras PN");
  log("OK  ativo cadastrado pela tela (símbolo normalizado para maiúsculas)");

  // compra pela tela: 10 a R$ 20, no passado
  await page.getByRole("button", { name: "Operações e valor" }).click();
  await page.locator('[id^="op-date-"]').fill(iso(start));
  await page.locator('[id^="op-qty-"]').fill("10");
  await page.locator('[id^="op-price-"]').fill("20");
  await page.getByRole("combobox", { name: "Conta de caixa da operação" }).click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await page.getByRole("button", { name: "Registrar", exact: true }).click();
  await page.waitForSelector("text=Compra ·");
  const afterBuy = await api("GET", "/reports/balances", null, t);
  const cc = afterBuy.accounts.find((a) => a.name === "Corrente").balance;
  const corretora = afterBuy.accounts.find((a) => a.name === "Corretora").balance;
  check(cc === "9800.00" && corretora === "200.00", "compra moveu R$ 200 da corrente para a corretora", `saldos: ${cc} / ${corretora}`);
  await shot("m13-1-compra");

  // cotação REAL da brapi (sandbox, PETR4, sem token) + CDI REAL do BCB
  await page.getByRole("button", { name: "Atualizar cotações" }).click();
  await page.waitForSelector("text=requisições no mês", { timeout: 30000 });
  const portfolio = await api("GET", "/investments", null, t);
  const petr = portfolio.positions[0];
  check(petr.price_source === "brapi" && Number(petr.price) > 0, `cotação real da brapi: PETR4 = R$ ${petr.price}`, "sem cotação da brapi: " + JSON.stringify(petr).slice(0, 300));
  const bench = await api("GET", "/investments/benchmark", null, t);
  check(bench.cdi_return_pct !== null, `CDI real do BCB desde ${bench.since}: ${bench.cdi_return_pct}%`, "sem CDI: " + JSON.stringify(bench));

  // venda pela tela: 4 un. ao preço atual → ganho/perda realizado
  await page.locator('[id^="op-qty-"]').fill("4");
  await page.locator('[id^="op-price-"]').fill("30");
  await page.getByRole("combobox", { name: "Tipo da operação" }).click();
  await page.getByRole("option", { name: "Venda" }).click();
  await page.getByRole("combobox", { name: "Conta de caixa da operação" }).click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await page.getByRole("combobox", { name: "Categoria da operação" }).click();
  await page.getByRole("option", { name: "Ganho de capital" }).click();
  await page.getByRole("button", { name: "Registrar", exact: true }).click();
  await page.waitForSelector("text=ganho R$");
  const dre = await api("GET", `/reports/dre?start_date=${iso(start).slice(0, 8)}01&end_date=${iso(today)}`, null, t);
  check(dre.net_result === "40.00", "ganho de R$ 40 (4 × (30 − 20)) aparece uma vez no DRE", "DRE net_result = " + dre.net_result);
  await shot("m13-2-venda");

  // patrimônio
  await page.goto(WEB + "/net-worth");
  await page.waitForSelector("text=Investimentos (valor de mercado)");
  const text = (await page.locator("main").innerText()).replace(/\n/g, " ");
  check(/Petrobras PN/.test(text), "patrimônio lista o investimento pelo valor de mercado", "patrimônio sem o investimento");
  await shot("m13-3-patrimonio");
} catch (e) {
  fail(String(e).slice(0, 700));
  await shot("m13-erro").catch(() => {});
}
if (problems.length) { log("PROBLEMAS DE CONSOLE:"); problems.forEach((p) => log(" -", p)); }
await browser.close();
