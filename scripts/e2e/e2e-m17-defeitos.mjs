import { chromium } from "playwright";

// Marco 17, etapa 1 (doc 33): datas na tela, fuso dos formulários, título do Resumo e sem e-mail no subtítulo.
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `m17-${Date.now()}@example.com`;
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

// Relógio do navegador: último dia do mês atual, 22h30 em São Paulo (já é o dia seguinte, e o mês seguinte, em UTC).
const now = new Date();
const pad = (n) => String(n).padStart(2, "0");
const year = now.getFullYear();
const month = now.getMonth() + 1;
const lastDay = new Date(year, month, 0).getDate();
const ym = `${year}-${pad(month)}`;
const localToday = `${ym}-${pad(lastDay)}`;
const clock = new Date(`${localToday}T22:30:00-03:00`);

await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
const account = await api("POST", "/accounts", { name: "Corrente", type: "checking", opening_balance: "1000.00" }, token);
const market = await api("POST", "/categories", { name: "Mercado" }, token);
await api("POST", "/transactions", { account_id: account.id, category_id: market.id, type: "expense", amount: "100.00", occurred_at: `${ym}-03`, description: "Feira" }, token);
await api("POST", "/transactions", { account_id: account.id, category_id: market.id, type: "expense", amount: "40.00", occurred_at: `${ym}-03`, description: "Padaria" }, token);
await api("POST", "/transactions", { account_id: account.id, category_id: market.id, type: "expense", amount: "60.00", occurred_at: `${ym}-08`, description: "Mercado" }, token);
await api("POST", "/budgets", { category_id: market.id, month: ym, limit_amount: "500.00" }, token);
await api("POST", "/goals", { name: "Viagem", target_amount: "3000.00", target_date: `${year + 1}-07-15` }, token);

const dash = await api("GET", `/dashboard?start_date=${ym}-01&end_date=${localToday}`, null, token);
const dates = dash.balance_evolution.map((p) => p.date);
check(dates.length === 2 && new Set(dates).size === dates.length, "API: evolução com um ponto por dia (2 dias, 3 lançamentos)", `datas: ${dates.join(", ")}`);

const browser = await chromium.launch();
const problems = [];

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, timezoneId: "America/Sao_Paulo", locale: "pt-BR" });
  const page = await context.newPage();
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  await page.clock.install({ time: clock });

  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/calendar");
  const utcDay = await page.evaluate(() => new Date().toISOString().slice(0, 10));
  log(`    navegador: ${localToday} 22:30 em São Paulo; em UTC já é ${utcDay}`);

  // Resumo do mês
  await page.goto(WEB + "/dashboard");
  const h1 = page.locator("main h1").first();
  await h1.waitFor();
  check((await h1.innerText()) === "Resumo do mês", "título 'Resumo do mês' (não 'Dashboard')", `título: ${await h1.innerText()}`);
  const subtitle = page.locator("main h1 + p");
  await subtitle.waitFor();
  check(/^\d{2}\/\d{2}\/\d{4} a \d{2}\/\d{2}\/\d{4}$/.test(await subtitle.innerText()), `período formatado (${await subtitle.innerText()})`, `período: ${await subtitle.innerText()}`);

  // Lançamentos: data padrão local e datas da lista formatadas
  await page.goto(WEB + "/transactions");
  await page.locator("#occurred_at").waitFor();
  check(await page.locator("#occurred_at").inputValue() === localToday, `lançamento novo sugere hoje no fuso local (${localToday})`, `sugere ${await page.locator("#occurred_at").inputValue()}`);
  const main = await page.locator("main").innerText();
  check(main.includes(`03/${pad(month)}/${year}`) && !main.includes(`${ym}-03`), "lista de lançamentos com data dd/mm/aaaa", "data crua na lista");
  check(!main.includes(email), "sem e-mail no subtítulo (Lançamentos)", "e-mail ainda aparece");

  // Recorrências
  await page.goto(WEB + "/recurring");
  await page.locator("#next_occurrence_date").waitFor();
  check(await page.locator("#next_occurrence_date").inputValue() === localToday, "recorrência nova sugere hoje no fuso local", `sugere ${await page.locator("#next_occurrence_date").inputValue()}`);

  // Orçamentos: mês padrão local e mês da lista legível
  await page.goto(WEB + "/budgets");
  await page.locator("#month").waitFor();
  check(await page.locator("#month").inputValue() === ym, `orçamento novo sugere o mês local (${ym}), não o seguinte`, `sugere ${await page.locator("#month").inputValue()}`);
  await page.getByText("Mercado", { exact: false }).first().waitFor();
  const months = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  check((await page.locator("main").innerText()).includes(`${months[month - 1]}/${year} ·`), "orçamento mostra o mês como mmm/aaaa", "mês cru no orçamento");

  // Metas: prazo formatado e data do aporte local
  await page.goto(WEB + "/goals");
  await page.getByText("Viagem").waitFor();
  check((await page.locator("main").innerText()).includes(`prazo 15/07/${year + 1}`), "meta mostra o prazo dd/mm/aaaa", "prazo cru na meta");
  await page.getByRole("button", { name: "Contribuir" }).click();
  const contributionDate = page.locator("main input[type=date]").last();
  check(await contributionDate.inputValue() === localToday, "aporte em meta sugere hoje no fuso local", `sugere ${await contributionDate.inputValue()}`);

  // Nenhuma das 7 telas mostra o e-mail
  const withEmail = [];
  for (const href of ["/accounts", "/categories", "/budgets", "/goals", "/recurring", "/commitments", "/transactions"]) {
    await page.goto(WEB + href);
    await page.locator("main h1").first().waitFor();
    await page.waitForTimeout(300);
    if ((await page.locator("main").innerText()).includes(email)) withEmail.push(href);
  }
  check(withEmail.length === 0, "nenhuma das 7 telas mostra o e-mail", "e-mail em " + withEmail.join(", "));
} catch (e) {
  fail(e.message);
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
