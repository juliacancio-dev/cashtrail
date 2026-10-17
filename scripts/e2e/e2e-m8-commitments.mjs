import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = "http://localhost:8020";
const WEB = "http://localhost:3000";
const email = `e2e-${Date.now()}@example.com`;
const password = "supersecret1";

const log = (...a) => console.log(...a);
const fail = (msg) => { console.log("FALHA:", msg); process.exitCode = 1; };

async function api(pathname, body, token) {
  const res = await fetch(API + pathname, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${pathname} -> ${res.status} ${await res.text()}`);
  return res.json();
}

// dados de base criados pela API (contas e categorias já têm tela própria e teste próprio)
await api("/auth/register", { email, password });
const { access_token } = await api("/auth/login", { email, password });
await api("/accounts", { name: "Corrente", type: "checking" }, access_token);
await api("/categories", { name: "Moradia" }, access_token);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1100, height: 1000 } });
const problems = [];
page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error") problems.push("console: " + m.text()); });

const shot = (name) => page.screenshot({ path: path.join(OUT, name + ".png"), fullPage: true });
const cards = () => page.locator("text=/parcela \\d\\/3/").count();

try {
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/accounts");

  await page.goto(WEB + "/commitments");
  await page.getByRole("button", { name: "Nova conta" }).click();
  const form = page.getByRole("form", { name: "Nova conta a pagar ou receber" });
  await form.locator("#description").fill("Aluguel");
  await form.locator("#amount").fill("100");
  await form.locator("#installments").fill("3");
  await form.getByRole("combobox").nth(1).click();
  await page.getByRole("option", { name: "Moradia" }).click();
  await shot("1-form");
  await form.getByRole("button", { name: "Criar parcelas" }).click();

  await page.waitForSelector("text=parcela 1/3");
  const created = await cards();
  created === 3 ? log("OK  3 parcelas criadas") : fail(`esperava 3 parcelas, vieram ${created}`);
  const amounts = await page.locator("text=/R\\$\\s*33,3[34]/").count();
  amounts >= 3 ? log("OK  valores 33,34 / 33,33 / 33,33 na tela") : fail("valores das parcelas não bateram");
  await shot("2-lista");

  // pagar a 1ª parcela (conta escolhida pelo Select)
  await page.getByRole("button", { name: "Pagar", exact: true }).first().click();
  const settle = page.getByRole("form", { name: "Registrar pagamento" });
  await settle.getByRole("combobox").click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await shot("3-baixa");
  await settle.getByRole("button", { name: "Confirmar pagamento" }).click();
  await page.waitForFunction(() => document.querySelectorAll("form[aria-label='Registrar pagamento']").length === 0);
  await page.waitForTimeout(600);
  const afterPay = await cards();
  afterPay === 2 ? log("OK  parcela paga saiu do filtro 'em aberto'") : fail(`esperava 2 em aberto, vieram ${afterPay}`);

  // baixa parcial de R$ 10 na parcela que sobrou primeiro
  await page.getByRole("button", { name: "Pagar", exact: true }).first().click();
  const partial = page.getByRole("form", { name: "Registrar pagamento" });
  await partial.getByRole("combobox").click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await partial.locator("input[type=number]").fill("10");
  const hint = await partial.locator("text=/Baixa parcial/").count();
  hint === 1 ? log("OK  aviso de baixa parcial apareceu") : fail("aviso de baixa parcial não apareceu");
  await partial.getByRole("button", { name: "Confirmar pagamento" }).click();
  await page.waitForSelector("text=/pago R\\$\\s*10,00/");
  log("OK  baixa parcial registrada: " + (await page.locator("text=/pago R\\$\\s*10,00/").first().innerText()).replace(/\s+/g, " "));
  await shot("4-parcial");

  // histórico e desfazer
  await page.getByRole("button", { name: /Baixas/ }).first().click();
  await page.getByRole("button", { name: "Desfazer" }).first().click();
  await page.getByRole("button", { name: "Apagar baixa e lançamento" }).click();
  await page.waitForTimeout(800);
  const stillPartial = await page.locator("text=/pago R\\$\\s*10,00/").count();
  stillPartial === 0 ? log("OK  desfazer baixa removeu o pagamento parcial") : fail("o pagamento parcial continuou na tela");

  // o lançamento criado/desfeito aparece (ou some) em /transactions
  await page.goto(WEB + "/transactions");
  await page.waitForSelector("text=Aluguel");
  const txs = await page.locator("text=Aluguel (1/3)").count();
  txs === 1 ? log("OK  lançamento da parcela paga aparece em Lançamentos") : fail(`lançamento esperado 1x, achei ${txs}`);
  const wrong = await page.locator("text=Aluguel (2/3)").count();
  wrong === 0 ? log("OK  lançamento da baixa desfeita não existe mais") : fail("lançamento da baixa desfeita ainda existe");

  // alerta no dashboard: uma conta atrasada e uma que vence hoje (as parcelas seguintes vencem em meses)
  const cats = await (await fetch(API + "/categories", { headers: { Authorization: `Bearer ${access_token}` } })).json();
  const iso = (offset) => { const d = new Date(); d.setDate(d.getDate() + offset); return d.toISOString().slice(0, 10); };
  await api("/commitments", { direction: "payable", description: "Luz", amount: "80.00", due_date: iso(-2), category_id: cats[0].id }, access_token);
  await api("/commitments", { direction: "receivable", description: "Freela", amount: "300.00", due_date: iso(3), category_id: cats[0].id }, access_token);
  await page.goto(WEB + "/dashboard");
  await page.waitForSelector("text=/vence\\(m\\) em 7 dias/", { timeout: 15000 });
  log("OK  alerta de vencimentos no dashboard");
  await shot("5-dashboard");
} catch (e) {
  fail(e.message);
  await shot("erro").catch(() => {});
}

log(problems.length ? "ERROS NO CONSOLE:\n" + problems.join("\n") : "OK  sem erros no console");
await browser.close();
