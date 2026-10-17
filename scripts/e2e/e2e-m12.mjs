import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = "http://localhost:8020";
const WEB = "http://localhost:3000";
const email = `m12-${Date.now()}@example.com`;
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
await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "2000" }, t);
const juros = await api("POST", "/categories", { name: "Juros", dre_group: "financial_expense" }, t);
await api(
  "POST",
  "/debts",
  {
    name: "Financiamento do carro",
    principal: "10000",
    contracted_at: iso(today),
    installments: 24,
    first_due_date: iso(firstDue),
    system: "price",
    monthly_rate: "1",
    interest_category_id: juros.id,
    payment_account_id: null,
    received_account_id: null,
  },
  t,
);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 1200 } });
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

  // cadastra o bem financiado pela tela
  await page.goto(WEB + "/assets");
  await page.getByRole("button", { name: "Novo bem" }).click();
  const form = page.getByRole("form", { name: "Novo bem" });
  await form.locator("#asset-name").fill("Carro");
  await form.locator("#asset-value").fill("30000");
  await form.getByRole("combobox").nth(1).click();
  await page.getByRole("option", { name: "Financiamento do carro" }).click();
  await form.getByRole("button", { name: "Cadastrar bem" }).click();
  await page.waitForSelector("text=financiado: Financiamento do carro");
  log("OK  bem cadastrado e vinculado ao financiamento");
  await shot("m12-1-bens");

  // balanço
  await page.goto(WEB + "/net-worth");
  await page.waitForSelector("text=Total dos passivos");
  const text = (await page.locator("main").innerText()).replace(/\n/g, " ");
  check(/R\$\s22\.000,00/.test(text), "patrimônio líquido R$ 22.000,00 (2.000 + 30.000 − 10.000)", "PL errado: " + text.slice(0, 500));
  check(/seu: R\$\s20\.000,00/.test(text), "bem mostra a parte sua (R$ 20.000,00)", "sem equity do bem");
  check(/curto prazo/.test(text), "dívida mostra curto e longo prazo", "sem curto/longo prazo");
  await shot("m12-2-patrimonio");

  // valorização do bem muda o PL
  await page.goto(WEB + "/assets");
  await page.getByRole("button", { name: "Avaliações" }).click();
  await page.getByLabel("Novo valor").fill("28000");
  await page.getByRole("button", { name: "Registrar avaliação" }).click();
  await page.waitForSelector("text=R$ 28.000,00 >> nth=0");
  await page.goto(WEB + "/net-worth");
  await page.waitForSelector("text=Total dos passivos");
  const text2 = (await page.locator("main").innerText()).replace(/\n/g, " ");
  check(/R\$\s20\.000,00/.test(text2) && /Patrimônio líquido em/.test(text2), "PL cai para R$ 20.000,00 após a nova avaliação", "PL após avaliação: " + text2.slice(0, 400));

  const dl = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar CSV" }).click();
  const file = await dl;
  check(file.suggestedFilename().startsWith("patrimonio-"), `CSV baixado (${file.suggestedFilename()})`, "CSV não baixou");

  await page.goto(WEB + "/dashboard");
  await page.waitForSelector("text=Patrimônio líquido");
  log("OK  dashboard mostra o patrimônio líquido");
  await shot("m12-3-dashboard");
} catch (e) {
  fail(String(e).slice(0, 700));
  await shot("m12-erro").catch(() => {});
}
if (problems.length) { log("PROBLEMAS DE CONSOLE:"); problems.forEach((p) => log(" -", p)); }
await browser.close();
