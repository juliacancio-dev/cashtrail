import { chromium } from "playwright";
import path from "node:path";

// Marco 17, etapa 2 (doc 33, decisão 8): cápsula Tinta + âmbar, gaveta no logo, busca, teclado, celular e contraste.
const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `nav-${Date.now()}@example.com`;
const password = "supersecret1";

// Mesmo agrupamento de frontend/src/components/app-shell/nav-config.ts.
const MODULES = {
  Calendário: [["/calendar", "Calendário do dinheiro"]],
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

// Contraste WCAG entre duas cores "rgb(r, g, b)".
function contrast(a, b) {
  const lum = (c) => {
    const [r, g, bl] = c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number).map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
  };
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}
const colors = (locator) => locator.evaluate((el) => {
  let bg = "rgba(0, 0, 0, 0)";
  for (let n = el; n && /rgba\(0, 0, 0, 0\)|transparent/.test(bg); n = n.parentElement) bg = getComputedStyle(n).backgroundColor;
  return { fg: getComputedStyle(el).color, bg };
});

const res = await fetch(API + "/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
if (!res.ok) throw new Error(`register -> ${res.status}`);

const browser = await chromium.launch();
const problems = [];

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light" });
  const page = await context.newPage();
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  await page.goto(WEB + "/login");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/calendar");

  const logo = page.getByRole("button", { name: "Abrir menu" });
  const modulesNav = page.getByRole("navigation", { name: "Módulos" });
  const drawer = page.locator("#menu-geral");
  const capsule = modulesNav.locator("xpath=..");

  // ---------- cápsula ----------
  check(await capsule.evaluate((el) => getComputedStyle(el).backgroundColor) === "rgb(24, 24, 27)", "cápsula em tinta (#18181b) no tema claro", "cor da cápsula errada no claro");
  const calendarPill = modulesNav.getByRole("link", { name: "Calendário", exact: true });
  check(await calendarPill.getAttribute("aria-current") === "true" && await calendarPill.evaluate((el) => getComputedStyle(el).backgroundColor) === "rgb(242, 181, 58)",
    "módulo atual é a pílula âmbar", "pílula do módulo atual sem âmbar");
  check(await logo.getAttribute("aria-expanded") === "false" && await logo.getAttribute("aria-controls") === "menu-geral", "logo é o botão do menu (aria-expanded, aria-controls)", "logo sem atributos de menu");

  // ---------- as 20 telas pela cápsula e pelas abas ----------
  let visited = 0;
  const misaligned = [];
  for (const [name, tabs] of Object.entries(MODULES)) {
    await modulesNav.getByRole("link", { name, exact: true }).click();
    await page.waitForURL((u) => pathOf(u) === tabs[0][0]);
    if (await modulesNav.getByRole("link", { name, exact: true }).getAttribute("aria-current") !== "true") fail(`${name}: pílula não marcada`);
    const tabsNav = page.getByRole("navigation", { name: `Telas de ${name}` });
    if (tabs.length === 1) {
      if (await tabsNav.count() !== 0) fail(`${name}: não devia ter linha de abas`);
      visited++;
      continue;
    }
    for (const [href, label] of tabs) {
      await tabsNav.getByRole("link", { name: label, exact: true }).click();
      await page.waitForURL((u) => pathOf(u) === href);
      await page.locator("main h1").first().waitFor({ timeout: 15000 });
      if (await tabsNav.getByRole("link", { name: label, exact: true }).getAttribute("aria-current") !== "page") fail(`${href}: aba não marcada`);
      const tabX = (await tabsNav.getByRole("link").first().boundingBox())?.x;
      const titleX = (await page.locator("main h1").first().boundingBox())?.x;
      if (tabX === undefined || titleX === undefined || Math.abs(tabX - titleX) > 2) misaligned.push(`${href} (aba ${tabX}, título ${titleX})`);
      visited++;
    }
  }
  check(visited === 21, "as 21 telas (calendário + 20) abriram pela cápsula e pelas abas, com a atual marcada", `${visited} telas em vez de 21`);
  check(misaligned.length === 0, "título de cada tela alinhado com a linha de abas", "desalinhado: " + misaligned.join(", "));

  // ---------- gaveta: abrir, foco, Tab preso, Esc ----------
  await page.goto(WEB + "/commitments");
  await page.locator("main h1").first().waitFor();
  await logo.click();
  await page.waitForFunction(() => document.activeElement?.getAttribute("aria-label") === "Fechar menu");
  check(await logo.getAttribute("aria-expanded") === "true" && !(await drawer.evaluate((el) => el.inert)), "clicar no logo abre a gaveta e leva o foco ao botão Fechar", "gaveta não abriu");
  check(await drawer.getByRole("link", { name: "A pagar e a receber" }).getAttribute("aria-current") === "page", "gaveta marca a tela atual", "tela atual não marcada na gaveta");
  const sectionHead = drawer.getByRole("heading", { name: "Caixa" });
  const sectionBg = (await colors(sectionHead)).bg;
  const drawerBg = await drawer.evaluate((el) => getComputedStyle(el).backgroundColor);
  check(sectionBg !== drawerBg, `cabeçalho de seção numa faixa mais escura (${sectionBg} sobre ${drawerBg})`, "cabeçalho de seção da mesma cor da gaveta");
  let escaped = false;
  for (let i = 0; i < 40; i++) {
    await page.keyboard.press("Tab");
    if (!(await page.evaluate(() => !!document.activeElement?.closest("#menu-geral")))) escaped = true;
  }
  check(!escaped, "Tab fica preso dentro da gaveta (40 tabs)", "o foco saiu da gaveta com Tab");
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => document.getElementById("menu-geral")?.inert === true);
  check(await page.evaluate(() => document.activeElement?.getAttribute("aria-label")) === "Abrir menu" && await logo.getAttribute("aria-expanded") === "false",
    "Esc fecha a gaveta e o foco volta ao logo", "Esc não fechou ou o foco se perdeu");

  // clique fora fecha
  await logo.click();
  await page.waitForFunction(() => document.getElementById("menu-geral")?.inert === false);
  await page.mouse.click(1200, 600);
  await page.waitForFunction(() => document.getElementById("menu-geral")?.inert === true);
  log("OK  clicar fora fecha a gaveta");

  // escolher uma tela navega e fecha
  await logo.click();
  await drawer.getByRole("link", { name: "Metas", exact: true }).click();
  await page.waitForURL((u) => pathOf(u) === "/goals");
  await page.waitForFunction(() => document.getElementById("menu-geral")?.inert === true);
  log("OK  escolher uma tela na gaveta leva até ela e fecha a gaveta");
  await page.screenshot({ path: path.join(OUT, "m17-nav-claro.png") });

  // ---------- busca e atalho / ----------
  await page.locator("main h1").first().waitFor();
  await page.keyboard.press("/");
  await page.waitForFunction(() => document.activeElement?.getAttribute("type") === "search");
  log("OK  a tecla / abre a gaveta já na busca");
  const search = drawer.getByRole("searchbox");
  await search.fill("transferencias");
  check(await drawer.getByRole("link").count() === 1 && await drawer.getByRole("link", { name: "Transferências" }).count() === 1,
    "busca ignora acento ('transferencias' acha Transferências)", `busca achou ${await drawer.getByRole("link").count()} links`);
  await search.fill("xyz");
  check(await drawer.getByText("Nenhuma tela com").count() === 1, "busca sem resultado avisa", "sem aviso de busca vazia");
  await search.fill("fluxo");
  await search.press("Enter");
  await page.waitForURL((u) => pathOf(u) === "/cash-flow");
  await page.waitForFunction(() => document.getElementById("menu-geral")?.inert === true);
  log("OK  Enter na busca vai para a primeira tela encontrada (Fluxo de caixa)");
  await page.locator("main h1").first().waitFor();
  await page.keyboard.press("/");
  await page.waitForFunction(() => document.activeElement?.getAttribute("type") === "search");
  check(await search.inputValue() === "", "a busca volta vazia ao reabrir", "busca guardou o texto anterior");
  await page.keyboard.press("Escape");

  // "/" não abre a gaveta enquanto se digita
  await page.goto(WEB + "/categories");
  const textInput = page.locator("main input[type=text], main input:not([type])").first();
  await textInput.waitFor();
  await textInput.click();
  await page.keyboard.type("a/b");
  check(await drawer.evaluate((el) => el.inert) && (await textInput.inputValue()).includes("/"), "/ digitado num campo fica no campo e não abre a gaveta", "/ abriu a gaveta durante a digitação");

  // ---------- contraste nos dois temas ----------
  async function contrastReport(theme) {
    const items = [];
    const pill = modulesNav.locator("[aria-current=true]");
    items.push(["pílula atual", contrast(...Object.values(await colors(pill)))]);
    const other = modulesNav.locator("a:not([aria-current])").first();
    items.push(["módulo apagado", contrast(...Object.values(await colors(other)))]);
    await logo.click();
    await page.waitForFunction(() => document.getElementById("menu-geral")?.inert === false);
    await page.waitForTimeout(500);
    items.push(["cabeçalho de seção", contrast(...Object.values(await colors(drawer.getByRole("heading", { name: "Caixa" }))))]);
    items.push(["tela na gaveta", contrast(...Object.values(await colors(drawer.getByRole("link", { name: "Lançamentos" }))))]);
    if (theme === "escuro") await page.screenshot({ path: path.join(OUT, "m17-nav-escuro.png") });
    await page.keyboard.press("Escape");
    const low = items.filter(([, c]) => c < 4.5);
    check(low.length === 0, `contraste no ${theme}: ` + items.map(([n, c]) => `${n} ${c.toFixed(1)}`).join(", "), `contraste baixo no ${theme}: ` + low.map(([n, c]) => `${n} ${c.toFixed(2)}`).join(", "));
  }
  await contrastReport("claro");
  await page.getByRole("button", { name: "Mudar para o modo escuro" }).first().click();
  await page.waitForTimeout(300);
  check(await capsule.evaluate((el) => getComputedStyle(el).backgroundColor) === "rgb(38, 38, 43)", "no escuro a cápsula fica em #26262b (não some no fundo)", "cor da cápsula errada no escuro");
  await contrastReport("escuro");

  // ---------- celular (mesma sessão: login tem limite de 5 por minuto) ----------
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(WEB + "/transactions");
  await page.locator("main h1").first().waitFor();
  const visiblePills = await modulesNav.getByRole("link").evaluateAll((els) => els.filter((e) => e.offsetParent !== null).map((e) => e.textContent));
  check(visiblePills.length === 1 && visiblePills[0] === "Caixa", "celular: a cápsula mostra só o módulo atual", "celular: pílulas visíveis " + visiblePills.join(", "));
  check(!(await capsule.locator("xpath=..").getByRole("button", { name: "Sair" }).isVisible()), "celular: Sair fora da cápsula (fica na gaveta)", "celular: Sair visível na cápsula");
  await logo.click();
  await page.waitForTimeout(500);
  const box = await drawer.boundingBox();
  check(box && box.x >= 0 && box.width < 390, `celular: gaveta cabe na tela (${Math.round(box?.width ?? 0)}px de 390)`, "celular: gaveta maior que a tela");
  await page.screenshot({ path: path.join(OUT, "m17-nav-celular.png") });
  await page.keyboard.press("Escape");
  const overflow = [];
  for (const href of Object.values(MODULES).flat().map(([h]) => h)) {
    await page.goto(WEB + href);
    await page.locator("main").first().waitFor({ timeout: 15000 });
    await page.waitForTimeout(150);
    const wide = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (wide > 1) overflow.push(`${href} (+${wide}px)`);
  }
  check(overflow.length === 0, "celular: nenhuma das 21 telas rola na horizontal", "celular: rolagem horizontal em " + overflow.join(", "));

  // ---------- menos movimento ----------
  await page.emulateMedia({ reducedMotion: "reduce" });
  const motion = await page.evaluate(() => ({
    drawer: getComputedStyle(document.getElementById("menu-geral")).transitionProperty,
    ping: getComputedStyle(document.querySelector(".nav-ping")).animationName,
  }));
  check(motion.drawer === "none" && motion.ping === "none", "com 'reduzir movimento' a gaveta abre sem animação e o anel não pisca", `movimento: ${JSON.stringify(motion)}`);
  await page.emulateMedia({ reducedMotion: "no-preference" });

  // ---------- sair pela gaveta ----------
  await page.setViewportSize({ width: 390, height: 844 });
  await logo.click();
  await drawer.getByRole("button", { name: "Sair" }).click();
  await page.waitForURL("**/login");
  log("OK  celular: Sair pela gaveta leva ao login");
} catch (e) {
  fail(e.message);
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
