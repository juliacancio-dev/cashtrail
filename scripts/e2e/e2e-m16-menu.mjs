import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `menu-${Date.now()}@example.com`;
const password = "supersecret1";

// Mesmo agrupamento de frontend/src/components/app-shell/nav-config.ts (doc 32, decisão 2).
const MODULES = {
  Caixa: [["/dashboard", "Resumo do mês"], ["/transactions", "Lançamentos"], ["/categories", "Categorias"], ["/transfers", "Transferências"], ["/import", "Importar extrato"]],
  Compromissos: [["/commitments", "A pagar e a receber"], ["/cards", "Cartões e faturas"], ["/recurring", "Recorrências"], ["/debts", "Dívidas"]],
  Patrimônio: [["/accounts", "Contas"], ["/assets", "Bens"], ["/investments", "Investimentos"], ["/net-worth", "Balanço"]],
  Planejamento: [["/budgets", "Orçamentos"], ["/goals", "Metas"], ["/retirement", "Independência"], ["/insurance", "Seguros"]],
  Relatórios: [["/dre", "DRE"], ["/cash-flow", "Fluxo de caixa"], ["/tax", "Imposto de renda"]],
};

const log = (...a) => console.log(...a);
const fail = (msg) => { console.log("FALHA:", msg); process.exitCode = 1; };
const check = (ok, good, bad) => (ok ? log("OK  " + good) : fail(bad));
const pathOf = (url) => new URL(url).pathname.replace(/\/+$/, "") || "/";

const res = await fetch(API + "/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
if (!res.ok) throw new Error(`register -> ${res.status}`);

const browser = await chromium.launch();
const problems = [];

async function login(page) {
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/calendar");
}

try {
  // ---------- desktop ----------
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  await login(page);
  const modulesNav = page.getByRole("navigation", { name: "Módulos" });
  const box = await modulesNav.boundingBox();
  check(box && box.height < 60, `menu de módulos em uma linha só (${Math.round(box?.height ?? 0)}px de altura)`, "menu quebrou em mais de uma linha");
  check(await page.locator("header").count() === 1, "um cabeçalho só na página (sem menu repetido)", "cabeçalho duplicado");
  check(await page.getByRole("button", { name: /Mudar para o modo/ }).count() === 1, "botão de tema no cabeçalho", "botão de tema sumiu");

  let visited = 0;
  for (const [name, tabs] of Object.entries(MODULES)) {
    await modulesNav.getByRole("link", { name, exact: true }).click();
    await page.waitForURL((u) => pathOf(u) === tabs[0][0]);
    const tabsNav = page.getByRole("navigation", { name: `Telas de ${name}` });
    check(await modulesNav.getByRole("link", { name, exact: true }).getAttribute("aria-current") === "true", `${name}: módulo marcado como atual`, `${name}: módulo não marcado`);
    for (const [href, label] of tabs) {
      await tabsNav.getByRole("link", { name: label, exact: true }).click();
      await page.waitForURL((u) => pathOf(u) === href);
      await page.locator("h1").first().waitFor({ timeout: 15000 });
      const current = await tabsNav.getByRole("link", { name: label, exact: true }).getAttribute("aria-current");
      if (current !== "page") fail(`${href}: aba não marcada como atual`);
      // O título da página começa na mesma coluna que o nome do app no cabeçalho.
      const brandX = (await page.locator("header").getByText("CashTrail", { exact: true }).boundingBox())?.x;
      const titleX = (await page.locator("main h1").first().boundingBox())?.x;
      if (brandX === undefined || titleX === undefined || Math.abs(brandX - titleX) > 2) {
        fail(`${href}: título desalinhado do cabeçalho (cabeçalho ${brandX}, título ${titleX})`);
      }
      visited++;
    }
  }
  check(visited === 20, "as 20 telas abriram pelo menu e pelas abas, com a aba atual marcada e o título alinhado ao cabeçalho", `só ${visited} telas abertas`);
  await page.goto(WEB + "/transactions");
  await page.locator("h1").first().waitFor();
  await page.screenshot({ path: path.join(OUT, "m16-menu-desktop.png"), fullPage: true });

  // ---------- celular ----------
  const phone = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  phone.on("pageerror", (e) => problems.push("pageerror (celular): " + e.message));
  await login(phone);
  check(!(await phone.getByRole("navigation", { name: "Módulos" }).isVisible()), "celular: links dos módulos escondidos, só o botão Menu", "celular: menu de módulos visível sem abrir");
  const menuButton = phone.getByRole("button", { name: "Menu" });
  await menuButton.click();
  check(await phone.getByRole("button", { name: "Fechar" }).getAttribute("aria-expanded") === "true", "celular: Menu abre a lista (aria-expanded)", "celular: aria-expanded não mudou");
  await phone.screenshot({ path: path.join(OUT, "m16-menu-celular-aberto.png") });
  await phone.locator("#menu-celular").getByRole("link", { name: "DRE", exact: true }).click();
  await phone.waitForURL((u) => pathOf(u) === "/dre");
  check(await phone.locator("#menu-celular").count() === 0, "celular: escolher uma tela leva até ela e fecha o menu", "celular: menu continuou aberto");

  const overflow = [];
  for (const href of Object.values(MODULES).flat().map(([h]) => h)) {
    await phone.goto(WEB + href);
    await phone.locator("h1").first().waitFor({ timeout: 15000 });
    const wide = await phone.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (wide > 1) overflow.push(`${href} (+${wide}px)`);
  }
  check(overflow.length === 0, "celular: nenhuma das 20 telas rola na horizontal", "celular: rolagem horizontal em " + overflow.join(", "));
  await phone.goto(WEB + "/transactions");
  await phone.locator("h1").first().waitFor();
  await phone.screenshot({ path: path.join(OUT, "m16-menu-celular.png"), fullPage: true });

  // ---------- sair ----------
  await page.getByRole("button", { name: "Sair" }).click();
  await page.waitForURL("**/login");
  log("OK  Sair leva ao login");
} catch (e) {
  fail(e.message);
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
