import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `cores-${Date.now()}@example.com`;
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

const now = new Date();
const pad = (n) => String(n).padStart(2, "0");
const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const daysAgo = (n) => iso(new Date(now.getFullYear(), now.getMonth(), now.getDate() - n));

// Cenário com receita, despesa, conta vencida, conta paga e fatura de cartão.
await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
const checking = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "1000.00" }, token);
const card = await api("POST", "/accounts", { name: "Cartão", type: "credit_card" }, token);
const cardConfig = await api("POST", "/cards", { account_id: card.id, closing_day: 5, due_day: 12, default_payment_account_id: checking.id }, token);
const salary = await api("POST", "/categories", { name: "Salário" }, token);
const market = await api("POST", "/categories", { name: "Mercado" }, token);
const home = await api("POST", "/categories", { name: "Moradia" }, token);
await api("POST", "/transactions", { account_id: checking.id, category_id: salary.id, type: "income", amount: "3000.00", occurred_at: daysAgo(3), description: "Salário" }, token);
await api("POST", "/transactions", { account_id: checking.id, category_id: market.id, type: "expense", amount: "400.00", occurred_at: daysAgo(2), description: "Mercado" }, token);
await api("POST", "/transactions", { account_id: checking.id, category_id: home.id, type: "expense", amount: "900.00", occurred_at: daysAgo(1), description: "Aluguel" }, token);
await api("POST", "/commitments", { direction: "payable", description: "IPTU", amount: "200.00", due_date: daysAgo(10), category_id: home.id }, token);
const paid = (await api("POST", "/commitments", { direction: "payable", description: "Internet", amount: "120.00", due_date: daysAgo(1), category_id: home.id }, token))[0];
await api("POST", `/commitments/${paid.id}/settlements`, { account_id: checking.id, paid_at: daysAgo(1) }, token);
await api("POST", `/cards/${cardConfig.id}/purchases`, { description: "TV", amount: "600.00", purchase_date: daysAgo(1), category_id: market.id }, token);

const TOKENS = {
  light: { income: "rgb(20, 108, 60)", expense: "rgb(180, 35, 24)", warning: "rgb(138, 83, 0)", info: "rgb(31, 91, 184)", chart1: "#2a78d6" },
  dark: { income: "rgb(91, 211, 138)", expense: "rgb(255, 138, 122)", warning: "rgb(245, 196, 81)", info: "rgb(141, 180, 255)", chart1: "#3987e5" },
};

// Contraste WCAG do texto contra o fundo efetivo (sobe na árvore até achar um fundo opaco,
// compondo fundos translúcidos como os chips).
const contrastOf = (locator) =>
  locator.evaluate((el) => {
    const parse = (c) => (c.match(/[\d.]+/g) || []).map(Number);
    const lum = ([r, g, b]) => {
      const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
      return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
    };
    const layers = [];
    for (let node = el; node; node = node.parentElement) {
      const [r, g, b, a = 1] = parse(getComputedStyle(node).backgroundColor);
      if (a > 0) layers.push([r, g, b, a]);
      if (a >= 1) break;
    }
    let bg = [255, 255, 255];
    for (const [r, g, b, a] of layers.reverse()) bg = [r * a + bg[0] * (1 - a), g * a + bg[1] * (1 - a), b * a + bg[2] * (1 - a)];
    // Texto SVG (eixos) é pintado pelo fill, não pelo color.
    const fg = parse(el instanceof SVGElement ? getComputedStyle(el).fill : getComputedStyle(el).color);
    const [hi, lo] = [lum(fg), lum(bg)].sort((x, y) => y - x);
    return { color: el instanceof SVGElement ? getComputedStyle(el).fill : getComputedStyle(el).color, ratio: (hi + 0.05) / (lo + 0.05) };
  });

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

  for (const mode of ["light", "dark"]) {
    await page.evaluate((m) => { localStorage.setItem("theme", m); }, mode);
    const t = TOKENS[mode];
    const tag = mode === "light" ? "claro" : "escuro";

    // Lançamentos: receita e despesa.
    await page.goto(WEB + "/transactions");
    await page.getByText("Salário").first().waitFor();
    const isDark = await page.evaluate(() => document.documentElement.classList.contains("dark"));
    check(isDark === (mode === "dark"), `${tag}: tema aplicado`, `${tag}: tema não aplicado`);
    const income = await contrastOf(page.locator("p.text-income").first());
    const expense = await contrastOf(page.locator("p.text-expense").first());
    check(income.color === t.income && income.ratio >= 4.5, `${tag}: receita no token (${income.ratio.toFixed(2)}:1)`, `${tag}: receita ${income.color} ${income.ratio.toFixed(2)}:1`);
    check(expense.color === t.expense && expense.ratio >= 4.5, `${tag}: despesa no token (${expense.ratio.toFixed(2)}:1)`, `${tag}: despesa ${expense.color} ${expense.ratio.toFixed(2)}:1`);

    // A pagar e a receber: chips de situação (vencida, paga).
    await page.goto(WEB + "/commitments");
    await page.getByText("IPTU").first().waitFor();
    // A tela abre em "Em aberto"; "Todos" traz também a conta quitada (desde o Marco 17 o filtro fica em "Filtros").
    await page.getByRole("button", { name: /^Filtros/ }).click();
    await page.getByRole("group", { name: "Filtros" }).getByRole("combobox").nth(0).click();
    await page.getByRole("option", { name: "Todos", exact: true }).click();
    await page.getByText("Internet").first().waitFor();
    const paidChip = page.locator("[class*='bg-income/12']").first();
    const overdueChip = page.locator("[class*='bg-destructive/10']").first();
    const pc = await contrastOf(paidChip);
    const oc = await contrastOf(overdueChip);
    check(pc.color === t.income && pc.ratio >= 4.5, `${tag}: chip "paga" legível (${pc.ratio.toFixed(2)}:1)`, `${tag}: chip paga ${pc.color} ${pc.ratio.toFixed(2)}:1`);
    check(oc.ratio >= 4.5, `${tag}: chip "vencida" legível (${oc.ratio.toFixed(2)}:1)`, `${tag}: chip vencida ${oc.ratio.toFixed(2)}:1`);
    await page.screenshot({ path: path.join(OUT, `m16-cores-${tag}-compromissos.png`), fullPage: true });

    // Resumo do mês (desde o Marco 17, etapa 3: barras horizontais em HTML): numa cor só, a do token, e valores legíveis.
    await page.goto(WEB + "/dashboard");
    await page.locator("[data-bar]").first().waitFor({ timeout: 15000 });
    const fills = await page.locator("[data-bar]").evaluateAll((els) => els.map((e) => getComputedStyle(e).backgroundColor));
    const expected = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--chart-1").trim());
    check(expected === t.chart1, `${tag}: --chart-1 é ${t.chart1}`, `${tag}: --chart-1 = ${expected}`);
    check(fills.length >= 2 && new Set(fills).size === 1, `${tag}: ${fills.length} barras de categoria na mesma cor`, `${tag}: cores das barras ${[...new Set(fills)].join(", ")}`);
    const value = await contrastOf(page.getByRole("region", { name: "Gasto por categoria" }).locator("li > span:last-child").first());
    check(value.ratio >= 4.5, `${tag}: valores das categorias legíveis (${value.ratio.toFixed(2)}:1)`, `${tag}: valor ${value.ratio.toFixed(2)}:1`);
    await page.screenshot({ path: path.join(OUT, `m16-cores-${tag}-resumo.png`), fullPage: true });
  }
} catch (e) {
  fail(e.message);
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
