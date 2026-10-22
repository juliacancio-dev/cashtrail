import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `m11-${Date.now()}@example.com`;
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
const firstDue = new Date(today.getTime() + 10 * 86400000);

await api("POST", "/auth/register", { email, password });
const { access_token: t } = await api("POST", "/auth/login", { email, password });
const acc = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "5000" }, t);
await api("POST", "/categories", { name: "Juros", dre_group: "financial_expense" }, t);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 1100 } });
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

  await page.goto(WEB + "/debts");
  await page.getByRole("button", { name: "Nova dívida" }).click();
  const form = page.getByRole("form", { name: "Nova dívida" });
  await form.locator("#debt-name").fill("Emprestimo pessoal");
  await form.locator("#debt-creditor").fill("Banco X");
  await form.locator("#debt-principal").fill("1000");
  await form.locator("#debt-installments").fill("12");
  await form.locator("#debt-first-due").fill(iso(firstDue));
  await form.locator("#debt-rate").fill("2");
  await form.getByRole("combobox").nth(1).click();
  await page.getByRole("option", { name: "Juros" }).click();
  await form.getByRole("combobox").nth(2).click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await form.getByRole("combobox").nth(3).click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await form.getByRole("button", { name: "Simular parcelas" }).click();
  await page.waitForSelector("text=Total a pagar");
  const sim = await form.innerText();
  check(/94,56/.test(sim), "simulação mostra a parcela Price de R$ 94,56", "simulação sem 94,56: " + sim.slice(0, 300));
  await shot("m11-1-simulacao");
  await form.getByRole("button", { name: "Cadastrar dívida" }).click();
  await page.waitForSelector("text=Emprestimo pessoal");
  const card = await page.locator("main").innerText();
  check(/Saldo devedor\s*R\$\s*1\.000,00/.test(card.replace(/\n/g, " ")), "dívida criada com saldo devedor R$ 1.000,00", "saldo devedor errado: " + card.slice(0, 400));

  // contas: saldo atual da corrente = 6.000, e a dívida aparece como saldo devedor
  await page.goto(WEB + "/accounts");
  await page.waitForSelector("text=Dívida (empréstimo/financiamento)");
  const accountsText = await page.locator("main").innerText();
  check(/6\.000,00/.test(accountsText), "conta corrente com R$ 6.000,00 (5.000 + 1.000 recebidos)", "corrente sem 6.000,00");

  // pagar parcela 1
  await page.goto(WEB + "/debts");
  await page.getByRole("button", { name: "Ver parcelas" }).click();
  await page.waitForSelector("text=Pagamentos extras, Simular", { timeout: 3000 }).catch(() => {});
  await page.getByRole("button", { name: "Pagar", exact: true }).first().click();
  await page.getByRole("button", { name: "Confirmar pagamento" }).click();
  await page.waitForSelector("text=paga >> nth=0");
  await page.waitForTimeout(800);
  const afterPay = (await page.locator("main").innerText()).replace(/\n/g, " ");
  check(/925,44/.test(afterPay), "após pagar a parcela 1 o saldo devedor é R$ 925,44", "saldo após pagamento errado: " + afterPay.slice(0, 500));
  await shot("m11-2-parcela-paga");

  // DRE: só juros
  const dre = await api("GET", `/reports/dre?start_date=${iso(today).slice(0, 8)}01&end_date=${iso(today)}`, null, t);
  check(dre.net_result === "-20.00", "DRE do mês: só R$ 20,00 de juros (principal fora do resultado)", "DRE net_result = " + dre.net_result);

  // amortização extra reduzindo prazo
  await page.getByLabel("Valor extra de principal").fill("400");
  await page.getByRole("button", { name: "Simular", exact: true }).click();
  await page.waitForSelector("text=Parcelas em aberto");
  await shot("m11-3-amortizacao");
  await page.getByRole("button", { name: "Confirmar pagamento extra" }).click();
  await page.waitForSelector("text=reduziu o prazo");
  const detail = await api("GET", "/debts", null, t);
  check(detail[0].outstanding === "525.44", "após extra de R$ 400 o saldo devedor é R$ 525,44", "saldo após extra = " + detail[0].outstanding);
  check(detail[0].installments_open < 11, `prazo caiu (${detail[0].installments_open} parcelas em aberto)`, "prazo não caiu");
  await shot("m11-4-final");

  // dashboard mostra o alerta
  await page.goto(WEB + "/dashboard");
  await page.waitForSelector("text=Dívidas: saldo devedor");
  log("OK  dashboard mostra o resumo das dívidas");
} catch (e) {
  fail(String(e).slice(0, 600));
  await shot("m11-erro").catch(() => {});
}
if (problems.length) { log("PROBLEMAS DE CONSOLE:"); problems.forEach((p) => log(" -", p)); }
await browser.close();
