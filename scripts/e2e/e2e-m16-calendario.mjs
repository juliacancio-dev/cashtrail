import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `cal-${Date.now()}@example.com`;
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

// Cenário no mês atual: salário no dia 1, mercado no dia 2, conta a pagar no último dia.
const now = new Date();
const pad = (n) => String(n).padStart(2, "0");
const ym = `${now.getFullYear()}-${pad(now.getMonth() + 1)}`;
const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
const todayIso = `${ym}-${pad(now.getDate())}`;

await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
const checking = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "1000.00" }, token);
const salary = await api("POST", "/categories", { name: "Salário" }, token);
const market = await api("POST", "/categories", { name: "Mercado" }, token);
await api("POST", "/transactions", { account_id: checking.id, category_id: salary.id, type: "income", amount: "3000.00", occurred_at: `${ym}-01`, description: "Salário" }, token);
await api("POST", "/transactions", { account_id: checking.id, category_id: market.id, type: "expense", amount: "400.00", occurred_at: `${ym}-02`, description: "Mercado" }, token);
await api("POST", "/commitments", { direction: "payable", description: "Internet", amount: "120.00", due_date: `${ym}-${pad(lastDay)}`, category_id: market.id }, token);
const cal = await api("GET", `/reports/calendar?month=${ym}`, null, token);

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
  log("OK  depois do login a pessoa cai no calendário");

  const modules = page.getByRole("navigation", { name: "Módulos" });
  check(await modules.getByRole("link", { name: "Calendário", exact: true }).getAttribute("aria-current") === "true",
    "Calendário é o primeiro módulo e está marcado", "Calendário não marcado no menu");
  check(await page.getByRole("navigation", { name: /^Telas de/ }).count() === 0, "sem linha de abas no calendário", "apareceu linha de abas");

  const summary = page.getByRole("region", { name: "Resumo" });
  await summary.waitFor();
  const summaryText = norm(await summary.innerText());
  check(summaryText.includes(brl(cal.cash_today)), `saldo de hoje igual ao da API (${brl(cal.cash_today)})`, `resumo: ${summaryText}`);
  const tight = `${cal.tightest_day.slice(8, 10)}/${cal.tightest_day.slice(5, 7)}`;
  check(summaryText.includes(tight) && summaryText.includes(brl(cal.tightest_balance)),
    `frase do dia mais apertado (${tight}, ${brl(cal.tightest_balance)})`, `resumo: ${summaryText}`);

  const grid = page.getByRole("group", { name: "Dias do mês" });
  check(await grid.getByRole("button").count() === lastDay, `${lastDay} dias no mês`, "quantidade de dias errada");
  const pressed = grid.locator("button[aria-pressed=true]");
  check((await pressed.getAttribute("aria-label")).startsWith(`${now.getDate()},`) , "abre com hoje selecionado", "hoje não veio selecionado");

  // Cada dia da tela mostra o saldo que a API calculou.
  let mismatches = 0;
  for (const d of cal.days) {
    const label = await grid.getByRole("button").nth(Number(d.day.slice(8, 10)) - 1).getAttribute("aria-label");
    if (!norm(label).includes(brl(d.balance)) || (d.is_tight && !label.includes("dia apertado"))) mismatches++;
  }
  check(mismatches === 0, "saldo e marca de dia apertado de todos os dias batem com a API", `${mismatches} dias divergentes`);
  const tightCount = cal.days.filter((d) => d.is_tight).length;
  check(tightCount <= Math.ceil(lastDay / 4), `no máximo um quarto do mês marcado como apertado (${tightCount})`, `${tightCount} dias apertados`);

  // Dia com movimento: o detalhe lista o lançamento e o saldo.
  await grid.getByRole("button").nth(1).click();
  const detail = page.getByRole("region", { name: "Dia selecionado" });
  const detailText = norm(await detail.innerText());
  check(detailText.includes("Mercado") && detailText.includes("− R$ 400,00") && detailText.includes(brl(cal.days[1].balance)),
    "clicar no dia 2 mostra o Mercado e o saldo do fim do dia", `detalhe: ${detailText}`);
  await page.screenshot({ path: path.join(OUT, "m16-calendario-claro.png"), fullPage: true });

  if (now.getDate() < lastDay) {
    await grid.getByRole("button").nth(lastDay - 1).click();
    const future = norm(await detail.innerText());
    check(future.includes("previsão com o que está agendado") && future.includes("Internet"),
      "dia futuro avisa que é previsão e mostra a conta a pagar", `detalhe: ${future}`);
  }

  // Próximo mês e volta para hoje.
  await page.getByRole("button", { name: "Próximo mês" }).click();
  await page.getByText(/previsto para o fim de/).waitFor();
  log("OK  próximo mês mostra o saldo previsto para o fim do mês");
  await page.getByRole("button", { name: "Hoje", exact: true }).click();
  await page.getByText("em caixa hoje.").waitFor();
  log("OK  botão Hoje volta ao mês atual");

  // Escuro.
  await page.getByRole("button", { name: "Mudar para o modo escuro" }).click();
  check(await page.evaluate(() => getComputedStyle(document.body).backgroundColor) === "rgb(17, 17, 19)", "calendário no modo escuro", "fundo escuro errado");
  await page.waitForTimeout(400); // deixa a transição de cor dos botões terminar antes da foto
  await page.screenshot({ path: path.join(OUT, "m16-calendario-escuro.png"), fullPage: true });

  // Celular: mesma sessão, janela estreita (sem novo login, que tem limite de 5 por minuto).
  const phone = page;
  await phone.setViewportSize({ width: 390, height: 844 });
  await phone.reload();
  await phone.getByRole("group", { name: "Dias do mês" }).waitFor();
  const overflow = await phone.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 0, "celular: calendário sem rolagem horizontal", `rola ${overflow}px`);
  await phone.screenshot({ path: path.join(OUT, "m16-calendario-celular.png"), fullPage: true });

  check(todayIso === cal.today, "relógio do navegador e do backend no mesmo dia", `navegador ${todayIso}, backend ${cal.today}`);
} catch (e) {
  fail(e.message);
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
