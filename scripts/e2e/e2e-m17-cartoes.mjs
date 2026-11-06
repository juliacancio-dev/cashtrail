import { chromium } from "playwright";
import path from "node:path";

// Marco 17, etapa 6 (doc 33, decisão 5): só a fatura atual aberta; as outras recolhidas.
const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `cart-${Date.now()}@example.com`;
const password = "supersecret1";

const log = (...a) => console.log(...a);
const fail = (msg) => { console.log("FALHA:", msg); process.exitCode = 1; };
const check = (ok, good, bad) => (ok ? log("OK  " + good) : fail(bad));

async function api(method, pathname, body, token) {
  const res = await fetch(API + pathname, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${pathname} -> ${res.status} ${await res.text()}`);
  return res.status === 204 ? null : res.json();
}
const pad = (n) => String(n).padStart(2, "0");
const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
const checking = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "5000.00" }, token);
const cardAccount = await api("POST", "/accounts", { name: "Nubank", type: "credit_card" }, token);
const cat = await api("POST", "/categories", { name: "Eletrônicos" }, token);
const card = await api("POST", "/cards", { account_id: cardAccount.id, closing_day: 8, due_day: 15, credit_limit: "8000.00", default_payment_account_id: checking.id }, token);
// Compra parcelada em 4x feita há 2 meses: faturas passadas, a atual e futuras.
const start = new Date(); start.setMonth(start.getMonth() - 2);
await api("POST", `/cards/${card.id}/purchases`, { description: "Notebook", amount: "2400.00", installments: 4, purchase_date: iso(start), category_id: cat.id }, token);
const invoices = await api("GET", `/cards/${card.id}/invoices`, null, token);

const browser = await chromium.launch();
const problems = [];
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/calendar");
  await page.goto(WEB + "/cards");
  await page.getByText("Nubank").first().waitFor();
  await page.getByText(/Fatura que fecha em/).first().waitFor();

  const visible = await page.getByText(/Fatura que fecha em/).count();
  const toggle = page.getByRole("button", { name: /Faturas anteriores e futuras/ });
  check(visible === 1 && invoices.length > 1, `só a fatura atual aberta (1 de ${invoices.length})`, `${visible} faturas visíveis`);
  check(await toggle.getAttribute("aria-expanded") === "false" && (await toggle.innerText()).includes(`· ${invoices.length - 1}`),
    "as outras recolhidas num botão com a contagem", "botão das outras faturas errado");
  // A API lista da mais nova para a mais antiga; a atual é a fechada não paga mais antiga, senão a aberta.
  const byClosing = [...invoices].sort((a, b) => a.closing_date.localeCompare(b.closing_date));
  const unpaid = byClosing.find((i) => (i.status === "overdue" || i.status === "closed") && Number(i.balance) > 0) ?? byClosing.find((i) => i.status === "open");
  const shown = await page.getByText(/Fatura que fecha em/).innerText();
  const [y, m, d] = unpaid.closing_date.split("-");
  check(shown.includes(`${d}/${m}/${y}`), `a aberta é a fatura atual (fecha em ${d}/${m}/${y})`, `fatura errada: ${shown}`);
  check(await page.getByRole("button", { name: "Ocultar faturas" }).count() === 0, "sem o botão antigo \"Ocultar faturas\"", "botão antigo ainda existe");

  await toggle.click();
  check(await page.getByText(/Fatura que fecha em/).count() === invoices.length, "abrir mostra todas as faturas", "faltam faturas ao abrir");
  await page.screenshot({ path: path.join(OUT, "m17-cartoes.png"), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  const wide = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(wide <= 1, "celular: sem rolagem horizontal", `celular: rola ${wide}px`);
} catch (e) {
  fail(e.message);
}
log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
