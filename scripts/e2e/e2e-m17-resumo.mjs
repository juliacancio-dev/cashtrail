import { chromium } from "playwright";
import path from "node:path";

// Marco 17, etapa 3 (doc 33, decisões 1 e 2): Resumo do mês com um número, uma frase, avisos, categorias e patrimônio.
const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `resumo-${Date.now()}@example.com`;
const password = "supersecret1";

const log = (...a) => console.log(...a);
const fail = (msg) => { console.log("FALHA:", msg); process.exitCode = 1; };
const check = (ok, good, bad) => (ok ? log("OK  " + good) : fail(bad));
const brl = (v) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v)).replace(/\s+/g, " ");
const norm = (s) => s.replace(/\s+/g, " ");
const MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

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
const ymOf = (offset) => { const d = new Date(now.getFullYear(), now.getMonth() + offset, 1); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`; };
const lastDayOf = (ym) => new Date(Number(ym.slice(0, 4)), Number(ym.slice(5, 7)), 0).getDate();
const iso = (offset) => { const d = new Date(now); d.setDate(d.getDate() + offset); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };
const thisMonth = ymOf(0), lastMonth = ymOf(-1), twoBack = ymOf(-2);

// ---------- dados ----------
await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
const account = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "2000.00" }, token);
const salary = await api("POST", "/categories", { name: "Salário" }, token);
// 9 categorias de despesa para a dobra em "Outras".
const spend = [["Moradia", 850], ["Mercado", 436.7], ["Saúde", 132], ["Restaurantes", 50], ["Lazer", 39.9], ["Transporte", 31.5], ["Educação", 20], ["Pets", 12], ["Presentes", 8]];
const cats = {};
for (const [name] of spend) cats[name] = await api("POST", "/categories", { name }, token);
const tx = (category, type, amount, occurred_at, description) =>
  api("POST", "/transactions", { account_id: account.id, category_id: category.id, type, amount: String(amount), occurred_at, description }, token);
await tx(salary, "income", 7500, `${thisMonth}-01`, "Salário");
for (const [name, amount] of spend) await tx(cats[name], "expense", amount, `${thisMonth}-01`, name);
// Mês passado no vermelho.
await tx(salary, "income", 1000, `${lastMonth}-05`, "Salário");
await tx(cats.Moradia, "expense", 1500, `${lastMonth}-10`, "Aluguel");
// Avisos: uma conta atrasada e uma que vence em 3 dias.
await api("POST", "/commitments", { direction: "payable", description: "Luz", amount: "214.60", due_date: iso(-3), category_id: cats.Moradia.id }, token);
await api("POST", "/commitments", { direction: "payable", description: "Internet", amount: "119.90", due_date: iso(3), category_id: cats.Moradia.id }, token);

const dashNow = await api("GET", `/dashboard?start_date=${thisMonth}-01&end_date=${thisMonth}-${lastDayOf(thisMonth)}`, null, token);
const dashLast = await api("GET", `/dashboard?start_date=${lastMonth}-01&end_date=${lastMonth}-${lastDayOf(lastMonth)}`, null, token);
const commitSum = await api("GET", "/commitments/summary", null, token);

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
  await page.goto(WEB + "/dashboard");

  const h1 = page.locator("main h1");
  const hero = page.getByRole("region", { name: "Resultado do mês" });
  await hero.waitFor();
  check(await h1.innerText() === `Resumo de ${MONTHS[now.getMonth()]}`, `título "Resumo de ${MONTHS[now.getMonth()]}"`, `título: ${await h1.innerText()}`);
  const heroText = norm(await hero.innerText());
  check(heroText.startsWith(brl(dashNow.summary.balance)) && heroText.includes("sobraram") && heroText.includes("até agora"),
    `número principal = sobra do mês da API (${brl(dashNow.summary.balance)})`, `resumo: ${heroText}`);
  check(heroText.includes(brl(dashNow.summary.income_total)) && heroText.includes(brl(dashNow.summary.expense_total)),
    "frase com quanto entrou e quanto saiu", `frase: ${heroText}`);

  // Avisos
  const attention = page.getByRole("region", { name: "Atenção" });
  const attentionText = norm(await attention.innerText());
  const toPay = Number(commitSum.payable.overdue_amount) + Number(commitSum.payable.due_soon_amount);
  check(attentionText.includes("1 conta atrasada e 1 vence nos próximos 7 dias") && attentionText.includes(brl(toPay)),
    `aviso de contas numa linha (${brl(toPay)} a pagar)`, `atenção: ${attentionText}`);
  check(await attention.getByRole("link").first().getAttribute("href") === "/commitments", "o aviso leva a Compromissos", "link do aviso errado");
  check(await attention.getByText("Atrasado:").count() === 1, "gravidade dita em texto para leitor de tela (não só a cor da bolinha)", "gravidade só na cor");

  // Categorias
  const bars = page.getByRole("region", { name: "Gasto por categoria" });
  const rows = await bars.locator("li").evaluateAll((els) => els.map((li) => ({
    name: li.children[0].textContent,
    value: li.children[2].textContent.replace(/\s+/g, " "),
    width: li.querySelector("[data-bar]").getBoundingClientRect().width,
    color: getComputedStyle(li.querySelector("[data-bar]")).backgroundColor,
  })));
  check(rows.length === 8 && rows[7].name === "Outras (2)" && rows[7].value === brl(20),
    "9 categorias viram 7 + \"Outras (2)\" com a soma das menores", `linhas: ${rows.map((r) => r.name).join(", ")}`);
  check(rows[0].name === "Moradia" && rows[0].value === brl(850) && rows.every((r, i) => i === 0 || r.width <= rows[i - 1].width + 0.5),
    "categorias do maior para o menor, barras proporcionais", "ordem ou tamanho errado");
  const chart1 = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--chart-1").trim());
  check(new Set(rows.map((r) => r.color)).size === 1, `barras numa cor só (${chart1})`, "barras com cores diferentes");
  const apiTotal = dashNow.by_category.reduce((s, c) => s + Number(c.total), 0);
  check(Math.abs(apiTotal - Number(dashNow.summary.expense_total)) < 0.01, "soma das categorias = despesas do mês", "categorias não somam as despesas");

  // Patrimônio e calendário
  const netWorth = page.getByRole("link", { name: /Patrimônio líquido/ });
  check(await netWorth.count() === 1 && await netWorth.getAttribute("href") === "/net-worth", "linha do patrimônio leva ao Balanço", "sem linha do patrimônio");
  check(await page.getByRole("link", { name: "Ver o saldo dia a dia no calendário" }).getAttribute("href") === "/calendar", "link para o saldo dia a dia no calendário", "sem link para o calendário");
  check(await page.locator(".recharts-wrapper").count() === 0 && await page.getByText("Evolução de saldo").count() === 0, "sem o gráfico \"Evolução de saldo\" (decisão 1)", "gráfico antigo ainda na tela");
  await page.screenshot({ path: path.join(OUT, "m17-resumo-claro.png"), fullPage: true });

  // Mês passado: negativo, sem avisos nem patrimônio
  await page.getByRole("button", { name: "Mês anterior" }).click();
  await page.getByText(`Resumo de ${MONTHS[Number(lastMonth.slice(5, 7)) - 1]}`).waitFor();
  await page.waitForFunction((v) => document.querySelector("[aria-label='Resultado do mês']")?.textContent.includes(v), brl(Math.abs(Number(dashLast.summary.balance))).replace(/\s/g, " "));
  const lastText = norm(await hero.innerText());
  const heroColor = await hero.locator("p").first().evaluate((el) => getComputedStyle(el).color);
  const expenseColor = await page.evaluate(() => { const d = document.createElement("span"); d.className = "text-expense"; document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; });
  check(lastText.startsWith("− " + brl(Math.abs(Number(dashLast.summary.balance)))) && lastText.includes("saiu mais do que entrou") && !lastText.includes("até agora") && heroColor === expenseColor,
    `mês negativo: "− ${brl(Math.abs(Number(dashLast.summary.balance)))}" em vermelho e "saiu mais do que entrou"`, `mês passado: ${lastText} (${heroColor})`);
  check(await page.getByRole("region", { name: "Atenção" }).count() === 0 && await page.getByRole("link", { name: /Patrimônio líquido/ }).count() === 0,
    "mês passado sem avisos e sem patrimônio (eles falam de hoje)", "avisos ou patrimônio num mês passado");

  // Dois meses atrás: vazio
  await page.getByRole("button", { name: "Mês anterior" }).click();
  await page.getByText(`Resumo de ${MONTHS[Number(twoBack.slice(5, 7)) - 1]}`).waitFor();
  await page.getByText(/Nenhum lançamento em/).waitFor();
  check(await page.getByText("Sem despesas no mês.").count() === 1, "mês vazio: \"Nenhum lançamento\" e \"Sem despesas no mês\"", "mês vazio sem aviso");
  await page.getByRole("button", { name: "Este mês" }).click();
  await page.getByText("até agora").waitFor();
  check(await page.getByRole("button", { name: "Este mês" }).count() === 0, "\"Este mês\" volta ao mês atual e some", "botão Este mês não sumiu");

  // Escuro: contraste do texto e cor da barra
  await page.getByRole("button", { name: "Mudar para o modo escuro" }).first().click();
  await page.waitForTimeout(400);
  const dark = await page.evaluate(() => ({
    bar: getComputedStyle(document.querySelector("[data-bar]")).backgroundColor,
    chart1: getComputedStyle(document.documentElement).getPropertyValue("--chart-1").trim(),
  }));
  check(dark.chart1 === "#3987e5", `no escuro as barras usam o --chart-1 do escuro (${dark.chart1}, ${dark.bar})`, `escuro: ${JSON.stringify(dark)}`);
  await page.screenshot({ path: path.join(OUT, "m17-resumo-escuro.png"), fullPage: true });

  // Celular
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await page.getByRole("region", { name: "Resultado do mês" }).waitFor();
  const wide = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(wide <= 1, "celular: sem rolagem horizontal", `celular: rola ${wide}px`);
  await page.screenshot({ path: path.join(OUT, "m17-resumo-celular.png"), fullPage: true });
} catch (e) {
  fail(e.message);
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
