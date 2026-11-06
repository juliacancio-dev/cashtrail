import { chromium } from "playwright";
import path from "node:path";

// Marco 17, etapa 5 (doc 33, decisão 4): frase de resumo, filtros recolhidos, grupos por vencimento, ação principal na linha.
const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `comp-${Date.now()}@example.com`;
const password = "supersecret1";

const log = (...a) => console.log(...a);
const fail = (msg) => { console.log("FALHA:", msg); process.exitCode = 1; };
const check = (ok, good, bad) => (ok ? log("OK  " + good) : fail(bad));
const brl = (v) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v)).replace(/\s+/g, " ");
const norm = (s) => s.replace(/\s+/g, " ");

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
const iso = (offset) => { const d = new Date(); d.setDate(d.getDate() + offset); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };

await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
const account = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "5000.00" }, token);
const home = await api("POST", "/categories", { name: "Moradia" }, token);
const work = await api("POST", "/categories", { name: "Serviços" }, token);
const add = (direction, description, amount, offset, category) =>
  api("POST", "/commitments", { direction, description, amount, due_date: iso(offset), category_id: category.id }, token);
await add("payable", "Conta de luz", "214.60", -3, home);
await add("payable", "Internet", "119.90", 2, home);
await add("receivable", "Freela", "1200.00", 3, work);
await add("payable", "Escola", "650.00", 20, home);
const summary = await api("GET", "/commitments/summary", null, token);

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
  await page.goto(WEB + "/commitments");
  await page.getByText("Conta de luz").waitFor();

  const sentence = norm(await page.locator("main p", { hasText: /^A pagar R/ }).innerText());
  check(sentence === `A pagar ${brl(summary.payable.open_amount)}, sendo 1 vencida. A receber ${brl(summary.receivable.open_amount)}.`, `frase: ${sentence}`, `frase errada: ${sentence}`);
  check(await page.getByText("Situação").count() === 0 && await page.getByRole("button", { name: "Filtros" }).getAttribute("aria-expanded") === "false",
    "filtros recolhidos: só Todas / A pagar / A receber e o botão Filtros", "filtros abertos de cara");

  const groups = await page.locator("main section h2").evaluateAll((els) => els.map((h) => h.textContent.replace(/\s+/g, " ").trim()));
  check(JSON.stringify(groups) === JSON.stringify(["Vencidas 1", "Próximos 7 dias 2", "Mais tarde 1"]), `grupos: ${groups.join(" / ")}`, `grupos errados: ${groups.join(" / ")}`);

  const light = page.locator("li", { hasText: "Conta de luz" });
  check(await light.getByRole("button", { name: "Pagar", exact: true }).isVisible() && await light.getByRole("button", { name: "Editar" }).count() === 0,
    "na linha só a ação principal (Pagar); Editar escondido", "linha com ações demais");
  await light.getByRole("button", { name: /Conta de luz/ }).click();
  check(await light.getByRole("button", { name: "Editar" }).isVisible() && await light.getByRole("button", { name: "Cancelar conta" }).isVisible(),
    "abrir a linha mostra Editar e Cancelar conta", "linha aberta sem ações");
  check(await page.locator("li", { hasText: "Freela" }).getByRole("button", { name: "Receber", exact: true }).count() === 1, "conta a receber tem o botão Receber", "sem Receber");

  // Pagar a luz: some de "Vencidas"; com "Todos" aparece em "Encerradas"
  await light.getByRole("button", { name: "Pagar", exact: true }).click();
  const settle = page.getByRole("form", { name: "Registrar pagamento" });
  await settle.getByRole("combobox").click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await settle.getByRole("button", { name: "Confirmar pagamento" }).click();
  await page.getByText(/^A pagar .*\. A receber/).filter({ hasNotText: "vencida" }).waitFor();
  check(await page.getByRole("heading", { name: /^Vencidas/ }).count() === 0, "conta paga sai do grupo Vencidas", "Vencidas ainda aparece");
  await page.getByRole("button", { name: "Filtros" }).click();
  await page.getByRole("group", { name: "Filtros" }).getByRole("combobox").nth(0).click();
  await page.getByRole("option", { name: "Todos", exact: true }).click();
  await page.getByRole("heading", { name: /^Encerradas/ }).waitFor();
  check(await page.getByRole("button", { name: "Filtros · 1" }).count() === 1, "com 'Todos', o botão mostra 'Filtros · 1' e a paga aparece em Encerradas", "contador de filtros errado");
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await page.getByRole("heading", { name: /^Encerradas/ }).waitFor({ state: "detached" });
  log("OK  Limpar filtros volta para 'Em aberto'");

  await page.getByRole("button", { name: "A receber", exact: true }).click();
  await page.getByText("Internet").waitFor({ state: "detached" });
  check(await page.getByText("Freela").count() === 1, "A receber mostra só o que é a receber", "filtro de direção errado");
  await page.screenshot({ path: path.join(OUT, "m17-compromissos.png"), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Todas", exact: true }).click();
  await page.getByText("Internet").waitFor();
  const wide = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(wide <= 1, "celular: sem rolagem horizontal", `celular: rola ${wide}px`);
} catch (e) {
  fail(e.message);
}
log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
