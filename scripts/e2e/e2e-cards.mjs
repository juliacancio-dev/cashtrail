import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = "http://localhost:8020";
const WEB = "http://localhost:3000";
const email = `cards-${Date.now()}@example.com`;
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

await api("POST", "/auth/register", { email, password });
const { access_token: token } = await api("POST", "/auth/login", { email, password });
await api("POST", "/accounts", { name: "Corrente", type: "checking" }, token);
await api("POST", "/accounts", { name: "Cartao Azul", type: "credit_card" }, token);
await api("POST", "/categories", { name: "Compras" }, token);

const dashboard = async () =>
  (await api("GET", "/dashboard?start_date=2026-03-01&end_date=2026-05-31", null, token)).summary;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1100, height: 1000 } });
const problems = [];
page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error") problems.push("console: " + m.text()); });
const shot = (name) => page.screenshot({ path: path.join(OUT, name + ".png"), fullPage: true });
const invoiceRow = (closing) => page.locator("div.rounded-lg.border", { hasText: `fecha em ${closing}` }).last();
const debtText = () => page.locator("text=Dívida do cartão").locator("xpath=following-sibling::p").first().innerText();

try {
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/accounts");

  // 1. configurar o cartão
  await page.goto(WEB + "/cards");
  await page.getByRole("button", { name: "Configurar cartão" }).first().click();
  const cardForm = page.getByRole("form", { name: "Configurar cartão" });
  await cardForm.locator("#closing_day").fill("5");
  await cardForm.locator("#due_day").fill("12");
  await cardForm.locator("#credit_limit").fill("1000");
  await cardForm.getByRole("combobox").nth(1).click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await cardForm.getByRole("button", { name: "Configurar cartão" }).click();
  await page.waitForSelector("text=Fecha dia 5 · vence dia 12");
  log("OK  cartão configurado (fecha dia 5, vence dia 12)");

  // 2. compra parcelada em 3x
  await page.getByRole("button", { name: "Nova compra" }).click();
  const purchase = page.getByRole("form", { name: "Nova compra no cartão" });
  await purchase.locator("#purchase-description").fill("Notebook");
  await purchase.locator("#purchase-amount").fill("300");
  await purchase.locator("#purchase-date").fill("2026-03-03");
  await purchase.locator("#purchase-installments").fill("3");
  await purchase.getByRole("combobox").click();
  await page.getByRole("option", { name: "Compras" }).click();
  await shot("c1-compra");
  await purchase.getByRole("button", { name: "Registrar compra" }).click();
  await page.waitForSelector("text=fecha em 05/05/2026");
  check((await debtText()).includes("300,00"), "dívida do cartão = R$ 300,00 (limite consumido pelo valor total)", "dívida não bateu: " + (await debtText()));
  const closings = await page.locator("text=/Fatura que fecha em/").allInnerTexts();
  check(["05/03/2026", "05/04/2026", "05/05/2026"].every((d) => closings.some((c) => c.includes(d))), "3 parcelas em 3 faturas (05/03, 05/04, 05/05)", "faturas esperadas ausentes: " + closings.join(" | "));
  check(await page.locator("text=/Disponível R\\$\\s*700,00 de R\\$\\s*1\\.000,00/").count() > 0, "limite disponível R$ 700,00 de R$ 1.000,00", "limite disponível não apareceu");
  const overdue = await page.locator("text=Vencida").count();
  check(overdue >= 3, "faturas passadas marcadas como Vencida (texto, não só cor)", `esperava 3 Vencida, vieram ${overdue}`);

  // 3. pagar a fatura de março: transferência, dashboard não muda
  const before = await dashboard();
  await invoiceRow("05/03/2026").getByRole("button", { name: "Pagar fatura" }).click();
  const payForm = page.getByRole("form", { name: "Pagar fatura" });
  await shot("c2-pagar");
  await payForm.getByRole("button", { name: "Confirmar pagamento" }).click();
  await page.waitForFunction(() => document.querySelectorAll("form[aria-label='Pagar fatura']").length === 0);
  await page.waitForTimeout(800);
  check((await debtText()).includes("200,00"), "dívida caiu para R$ 200,00 após pagar a fatura de março", "dívida após pagar: " + (await debtText()));
  const after = await dashboard();
  check(JSON.stringify(before) === JSON.stringify(after), `dashboard NÃO mudou ao pagar a fatura (receitas ${after.income_total}, despesas ${after.expense_total})`, `dashboard mudou: ${JSON.stringify(before)} -> ${JSON.stringify(after)}`);
  check((await invoiceRow("05/03/2026").innerText()).includes("Paga"), "fatura de março aparece como Paga", "fatura de março não ficou Paga");

  // 4. a transferência aparece na tela de transferências
  await page.goto(WEB + "/transfers");
  await page.waitForSelector("text=Corrente → Cartao Azul");
  check(await page.locator("text=/R\\$\\s*100,00/").count() > 0, "transferência Corrente → Cartao Azul de R$ 100,00 listada", "transferência do pagamento não apareceu");

  // 5. mover uma compra para a fatura seguinte
  await page.goto(WEB + "/cards");
  await page.waitForSelector("text=fecha em 05/04/2026");
  await invoiceRow("05/04/2026").getByRole("button", { name: "Ver compras e pagamentos" }).click();
  await page.waitForSelector("text=Notebook (2/3)");
  await invoiceRow("05/04/2026").getByRole("button", { name: "Mover para a fatura seguinte" }).click();
  await page.waitForTimeout(1200);
  const may = await invoiceRow("05/05/2026").innerText();
  check(/2 lançamento/.test(may), "compra movida: a fatura de maio passou a ter 2 lançamentos", "maio não ficou com 2 lançamentos: " + may.replace(/\s+/g, " "));
  await shot("c3-mover");

  // 6. desfazer o pagamento
  await invoiceRow("05/03/2026").getByRole("button", { name: "Ver compras e pagamentos" }).click();
  await page.waitForSelector("text=Pagamentos");
  await invoiceRow("05/03/2026").getByRole("button", { name: "Desfazer" }).click();
  await invoiceRow("05/03/2026").getByRole("button", { name: "Apagar pagamento e transferência" }).click();
  await page.waitForTimeout(1200);
  check((await debtText()).includes("300,00"), "desfazer pagamento: dívida voltou a R$ 300,00", "dívida após desfazer: " + (await debtText()));
  const transfers = await api("GET", "/transfers", null, token);
  check(transfers.length === 0, "desfazer pagamento apagou também a transferência", `restaram ${transfers.length} transferências`);

  // 7. transferência pela tela
  await page.goto(WEB + "/transfers");
  const tform = page.getByRole("form", { name: "Nova transferência" });
  await tform.getByRole("combobox").nth(0).click();
  await page.getByRole("option", { name: "Corrente" }).click();
  await tform.getByRole("combobox").nth(1).click();
  await page.getByRole("option", { name: "Cartao Azul" }).click();
  await tform.locator("#amount").fill("50");
  await tform.getByRole("button", { name: "Transferir" }).click();
  await page.waitForSelector("text=Corrente → Cartao Azul");
  log("OK  transferência criada pela tela");
  await page.getByRole("button", { name: "Desfazer" }).first().click();
  await page.getByRole("button", { name: "Confirmar" }).click();
  await page.waitForSelector("text=Nenhuma transferência registrada ainda.");
  log("OK  transferência desfeita pela tela");

  // 8. alerta no dashboard
  await page.goto(WEB + "/dashboard");
  await page.waitForSelector("text=/fatura\\(s\\) de cartão vencida\\(s\\)/", { timeout: 15000 });
  log("OK  alerta de faturas vencidas no dashboard");
  await shot("c4-dashboard");
} catch (e) {
  fail(e.message);
  await shot("erro-cards").catch(() => {});
}

log(problems.length ? "ERROS NO CONSOLE:\n" + problems.join("\n") : "OK  sem erros no console");
await browser.close();
