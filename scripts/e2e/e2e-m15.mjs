import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = "http://localhost:8020";
const WEB = "http://localhost:3000";
const email = `m15-${Date.now()}@example.com`;
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
const day = (n) => iso(new Date(Date.now() + n * 86400000));

await api("POST", "/auth/register", { email, password });
const { access_token: t } = await api("POST", "/auth/login", { email, password });
const cc = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "400000" }, t);
const corretora = await api("POST", "/accounts", { name: "Corretora", type: "investment" }, t);
await api("POST", "/categories", { name: "Seguros", dre_group: "fixed_expense" }, t);
await api("POST", "/assets", { name: "Carro", kind: "vehicle", current_value: "40000" }, t);
await api("POST", "/assets", { name: "Casa", kind: "real_estate", current_value: "400000" }, t);
const cdb = await api("POST", "/investments/assets", {
  account_id: corretora.id, name: "CDB", asset_class: "fixed_income", quote_source: "manual",
}, t);
await api("POST", `/investments/assets/${cdb.id}/operations`, {
  kind: "buy", occurred_at: day(-3), quantity: "1", unit_price: "300000", cash_account_id: cc.id,
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

  // apólice anual do carro pela tela, renovando em 15 dias
  await page.goto(WEB + "/insurance");
  await page.waitForSelector("text=Bens sem apólice ativa");
  await page.getByRole("button", { name: "Nova apólice" }).click();
  const form = page.getByRole("form", { name: "Nova apólice" });
  await form.locator("#pol-name").fill("Seguro do carro");
  await form.locator("#pol-insurer").fill("Seguradora X");
  await form.getByRole("combobox", { name: "Periodicidade do prêmio" }).click();
  await page.getByRole("option", { name: "Anual" }).click();
  await form.locator("#pol-premium").fill("2400");
  await form.locator("#pol-renews").fill(day(15));
  await form.getByRole("combobox", { name: "Categoria do prêmio" }).click();
  await page.getByRole("option", { name: "Seguros" }).click();
  await form.getByRole("combobox", { name: "Bem coberto" }).click();
  await page.getByRole("option", { name: "Carro" }).click();
  await form.getByRole("button", { name: "Cadastrar apólice" }).click();
  await page.waitForSelector("text=Seguro do carro");
  const commitments = await api("GET", "/commitments", null, t);
  check(commitments.items.length === 1 && commitments.items[0].amount === "2400.00",
    "prêmio anual virou uma conta a pagar de R$ 2.400 (uma só)", "conta a pagar não criada: " + JSON.stringify(commitments.items));
  await page.reload();
  await page.waitForSelector("text=Renova em até 30 dias");
  const text = (await page.locator("main").innerText()).replace(/\n/g, " ");
  check(/Bens sem apólice ativa:\s*Casa/.test(text), "Casa aparece como bem sem apólice (o carro está coberto)", "bens sem apólice: " + text.slice(0, 400));
  await shot("m15-1-seguros");

  // plano de independência financeira pela tela
  await page.goto(WEB + "/retirement");
  await page.waitForSelector("text=Premissas");
  await page.locator("#rt-age").fill("35");
  await page.locator("#rt-target-age").fill("55");
  await page.locator("#rt-income").fill("5000");
  await page.locator("#rt-benefit").fill("1000");
  await page.locator("#rt-contribution").fill("2000");
  await page.getByRole("button", { name: "Salvar e calcular" }).click();
  await page.waitForSelector("text=Patrimônio-alvo");
  const r = (await page.locator("main").innerText()).replace(/\n/g, " ");
  check(/R\$\s1\.200\.000,00/.test(r), "patrimônio-alvo R$ 1.200.000 ((5.000 − 1.000) × 12 ÷ 4%)", "alvo errado: " + r.slice(0, 500));
  check(/25,0%/.test(r), "progresso 25,0% (R$ 300.000 investidos)", "progresso errado");
  check(/IPCA dos últimos 12 meses/.test(r), "IPCA real do Banco Central como contexto", "sem IPCA");
  check(/Cenários/.test(r), "grade de cenários exibida", "sem cenários");
  await shot("m15-2-independencia");

  await page.goto(WEB + "/dashboard");
  await page.waitForSelector("text=renova(m) em até 30 dias");
  log("OK  dashboard avisa a renovação");
} catch (e) {
  fail(String(e).slice(0, 700));
  await shot("m15-erro").catch(() => {});
}
if (problems.length) { log("PROBLEMAS DE CONSOLE:"); problems.forEach((p) => log(" -", p)); }
await browser.close();
