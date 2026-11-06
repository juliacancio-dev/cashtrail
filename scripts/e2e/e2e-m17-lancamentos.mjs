import { chromium } from "playwright";
import path from "node:path";

// Marco 17, etapa 4 (doc 33, decisão 3): Lançamentos um mês por vez, agrupados por dia, formulário atrás do botão.
const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `lanc-${Date.now()}@example.com`;
const password = "supersecret1";

const log = (...a) => console.log(...a);
const fail = (msg) => { console.log("FALHA:", msg); process.exitCode = 1; };
const check = (ok, good, bad) => (ok ? log("OK  " + good) : fail(bad));
const brl = (v) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v)).replace(/\s+/g, " ");
const norm = (s) => s.replace(/\s+/g, " ");
const MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const WEEKDAYS = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];

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
const now = new Date();
const isoOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const ymOf = (offset) => { const d = new Date(now.getFullYear(), now.getMonth() + offset, 1); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`; };
const dayTitle = (iso) => { const [y, m, d] = iso.split("-").map(Number); return `${WEEKDAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()]}, ${d} de ${MONTHS[m - 1]}`; };
const today = isoOf(now);
const thisMonth = ymOf(0), lastMonth = ymOf(-1), twoBack = ymOf(-2);
const firstOfMonth = `${thisMonth}-01`;
const yesterday = isoOf(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1));
const hasYesterday = yesterday.startsWith(thisMonth) && yesterday !== firstOfMonth;

// ---------- dados ----------
await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
const account = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "1000.00" }, token);
const salary = await api("POST", "/categories", { name: "Salário" }, token);
const market = await api("POST", "/categories", { name: "Mercado" }, token);
const tx = (category, type, amount, occurred_at, description) =>
  api("POST", "/transactions", { account_id: account.id, category_id: category.id, type, amount: String(amount), occurred_at, description }, token);
await tx(salary, "income", 7500, firstOfMonth, "Salário");
if (today !== firstOfMonth) {
  await tx(market, "expense", 23.9, today, "Padaria");
  await tx(market, "expense", 132, today, "Farmácia");
}
if (hasYesterday) await tx(market, "expense", 412.8, yesterday, "Mercado da semana");
await tx(salary, "income", 1000, `${lastMonth}-05`, "Freela");
await tx(market, "expense", 300, `${lastMonth}-10`, "Feira");

const monthTx = await api("GET", `/transactions?start_date=${thisMonth}-01&end_date=${thisMonth}-31`.replace("-31", `-${pad(new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate())}`), null, token);

const browser = await chromium.launch();
const problems = [];

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 1000 }, colorScheme: "light" });
  const page = await context.newPage();
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/calendar");
  await page.goto(WEB + "/transactions");

  const h1 = page.locator("main h1");
  await page.getByText(/lançamentos? · entraram/).waitFor();
  check(await h1.innerText() === `Lançamentos de ${MONTHS[now.getMonth()]}`, `título "Lançamentos de ${MONTHS[now.getMonth()]}"`, `título: ${await h1.innerText()}`);
  const newButton = page.getByRole("button", { name: "Novo lançamento" });
  check(await newButton.getAttribute("aria-expanded") === "false" && await page.locator("#occurred_at").count() === 0, "formulário escondido atrás de \"Novo lançamento\"", "formulário aberto de cara");

  // Só o mês atual, com a frase de totais
  const income = monthTx.filter((t) => t.type === "income").reduce((s, t) => s + Number(t.amount), 0);
  const expense = monthTx.filter((t) => t.type === "expense").reduce((s, t) => s + Number(t.amount), 0);
  const sentence = norm(await page.getByText(/lançamentos? · entraram/).innerText());
  check(sentence.startsWith(`${monthTx.length} lançamento`) && sentence.includes(brl(income)) && sentence.includes(brl(expense)),
    `frase: ${sentence}`, `frase errada: ${sentence} (esperado ${monthTx.length}, ${brl(income)}, ${brl(expense)})`);
  check(await page.getByText("Freela").count() === 0, "lançamentos de outro mês não aparecem", "mês passado misturado na lista");

  // Agrupado por dia, do mais recente para o mais antigo
  const sections = await page.locator("main section[aria-label]").evaluateAll((els) => els.map((s) => ({
    label: s.getAttribute("aria-label"),
    total: s.querySelector("h2 span.font-mono")?.textContent.replace(/total do dia/, "").replace(/\s+/g, " ").trim(),
    rows: s.querySelectorAll("li").length,
  })));
  const days = [...new Set(monthTx.map((t) => t.occurred_at))].sort().reverse();
  check(sections.length === days.length && sections.every((s, i) => s.label.startsWith(dayTitle(days[i]))),
    `${days.length} dias, do mais recente para o mais antigo (${sections.map((s) => s.label).join(" / ")})`, `dias: ${JSON.stringify(sections)}`);
  if (today !== firstOfMonth) {
    const todaySection = sections.find((s) => s.label.startsWith(dayTitle(today)));
    check(todaySection?.label.endsWith("· hoje") && todaySection.total === `− ${brl(155.9)}` && todaySection.rows === 2,
      `hoje marcado, com 2 lançamentos e total do dia − ${brl(155.9)}`, `hoje: ${JSON.stringify(todaySection)}`);
  }
  if (hasYesterday) check(sections.some((s) => s.label === `${dayTitle(yesterday)} · ontem`), "ontem marcado", "ontem sem marca");
  const salaryRow = norm(await page.locator("li", { hasText: "Salário · Corrente" }).first().innerText());
  check(salaryRow.includes("+ " + brl(7500)) && await page.locator("li p.text-income").count() >= 1 && await page.locator("li p.text-expense").count() >= 1,
    "linha: descrição, \"Categoria · Conta\" e valor com sinal e cor", `linha: ${salaryRow}`);
  await page.screenshot({ path: path.join(OUT, "m17-lancamentos-claro.png"), fullPage: true });

  // Troca de mês e mês vazio
  await page.getByRole("button", { name: "Mês anterior" }).click();
  await page.getByText(`Lançamentos de ${MONTHS[Number(lastMonth.slice(5, 7)) - 1]}`).waitFor();
  await page.getByText("Feira").waitFor();
  check(norm(await page.getByText(/lançamentos? · entraram/).innerText()).startsWith("2 lançamentos") && await page.getByText("Padaria").count() === 0,
    "mês anterior mostra só os 2 lançamentos dele", "mês anterior errado");
  await page.getByRole("button", { name: "Mês anterior" }).click();
  await page.getByText(`Lançamentos de ${MONTHS[Number(twoBack.slice(5, 7)) - 1]}`).waitFor();
  await page.getByText("Nenhum lançamento neste mês.").waitFor();
  log("OK  mês sem lançamentos avisa");
  await page.getByRole("button", { name: "Este mês" }).click();
  await page.getByText("Salário · Corrente").waitFor();
  log("OK  \"Este mês\" volta ao mês atual");

  // Criar pelo formulário
  await newButton.click();
  const form = page.getByRole("region", { name: "Novo lançamento" });
  await form.locator("#occurred_at").waitFor();
  check(await page.getByRole("button", { name: "Fechar formulário" }).getAttribute("aria-expanded") === "true" && await form.locator("#occurred_at").inputValue() === today,
    "o botão abre o formulário, com a data de hoje", "formulário não abriu ou data errada");
  await form.getByRole("combobox").nth(0).click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await form.getByRole("combobox").nth(1).click();
  await page.getByRole("option", { name: "Mercado" }).click();
  await form.locator("#amount").fill("45.5");
  await form.locator("#description").fill("Açougue");
  await form.getByRole("button", { name: "Adicionar lançamento" }).click();
  await page.getByText("Açougue").waitFor();
  check(norm(await page.getByText(/lançamentos? · entraram/).innerText()).startsWith(`${monthTx.length + 1} lançamentos`) && await page.locator("section", { hasText: "Açougue" }).first().getAttribute("aria-label").then((l) => l.startsWith(dayTitle(today))),
    "lançamento novo aparece no dia de hoje e a contagem sobe", "lançamento novo não apareceu no lugar certo");

  // Data de outro mês: a tela vai até o mês dele
  await form.locator("#amount").fill("80");
  await form.locator("#description").fill("Conserto");
  await form.locator("#occurred_at").fill(`${lastMonth}-20`);
  await form.getByRole("button", { name: "Adicionar lançamento" }).click();
  await page.getByText(`Lançamentos de ${MONTHS[Number(lastMonth.slice(5, 7)) - 1]}`).waitFor();
  await page.getByText("Conserto").waitFor();
  log("OK  lançamento com data de outro mês leva a tela até aquele mês");

  // Celular
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Este mês" }).click();
  await page.getByText("Salário · Corrente").waitFor();
  const wide = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(wide <= 1, "celular: sem rolagem horizontal", `celular: rola ${wide}px`);
  await page.screenshot({ path: path.join(OUT, "m17-lancamentos-celular.png"), fullPage: true });
} catch (e) {
  fail(e.message);
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
