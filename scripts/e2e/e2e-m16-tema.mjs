import { chromium } from "playwright";
import path from "node:path";

const OUT = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const API = process.env.E2E_API ?? "http://localhost:8020";
const WEB = process.env.E2E_WEB ?? "http://localhost:3000";
const email = `tema-${Date.now()}@example.com`;
const password = "supersecret1";

const log = (...a) => console.log(...a);
const fail = (msg) => { console.log("FALHA:", msg); process.exitCode = 1; };
const check = (ok, good, bad) => (ok ? log("OK  " + good) : fail(bad));

const res = await fetch(API + "/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
if (!res.ok) throw new Error(`register -> ${res.status}`);

const browser = await chromium.launch();
// Sistema em modo escuro e nenhuma escolha salva: deve abrir escuro sem piscar.
const context = await browser.newContext({ colorScheme: "dark", viewport: { width: 1100, height: 900 } });
const page = await context.newPage();
const problems = [];
page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
const shot = (name) => page.screenshot({ path: path.join(OUT, name + ".png"), fullPage: true });
const html = () => page.evaluate(() => ({
  dark: document.documentElement.classList.contains("dark"),
  lang: document.documentElement.lang,
  bg: getComputedStyle(document.body).backgroundColor,
  font: getComputedStyle(document.body).fontFamily,
  saved: (() => { try { return localStorage.getItem("theme"); } catch { return "erro"; } })(),
}));

try {
  // 1. antes da hidratação: o script do <head> já aplicou o tema do sistema
  await page.goto(WEB + "/login", { waitUntil: "domcontentloaded" });
  let s = await html();
  check(s.dark, "sem escolha salva, segue o sistema (escuro) já no carregamento", "não aplicou o escuro do sistema");
  check(s.bg === "rgb(17, 17, 19)", "fundo escuro #111113", "fundo escuro inesperado: " + s.bg);
  check(s.lang === "pt-BR", "lang=pt-BR", "lang: " + s.lang);
  check(/Geist/.test(s.font), "fonte Geist aplicada (" + s.font.split(",")[0] + ")", "fonte não é Geist: " + s.font);

  // 2. entrar e usar o botão
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("**/calendar");
  await shot("m16-escuro");
  await page.getByRole("button", { name: "Mudar para o modo claro" }).click();
  s = await html();
  check(!s.dark && s.bg === "rgb(250, 250, 249)", "botão troca para o claro (#FAFAF9)", "não trocou para o claro: " + JSON.stringify(s));
  check(s.saved === "light", "escolha salva no navegador", "escolha não salva: " + s.saved);
  check(await page.getByRole("button", { name: "Mudar para o modo escuro" }).count() === 1, "rótulo do botão acompanha o tema", "rótulo não mudou");

  // 3. a escolha vale mais que o sistema, também depois de recarregar
  await page.reload({ waitUntil: "domcontentloaded" });
  s = await html();
  check(!s.dark, "depois de recarregar continua claro, mesmo com o sistema escuro", "voltou para o escuro ao recarregar");
  await page.goto(WEB + "/dashboard");
  await page.waitForSelector("text=Sair", { timeout: 15000 }).catch(() => {});
  await shot("m16-claro-dashboard");
  await page.getByRole("button", { name: "Mudar para o modo escuro" }).click();
  await shot("m16-escuro-dashboard");
  s = await html();
  check(s.dark && s.saved === "dark", "volta para o escuro e salva", "não voltou para o escuro: " + JSON.stringify(s));
} catch (e) {
  fail(e.message);
  await shot("erro-m16").catch(() => {});
}

log(problems.length ? "ERROS NA PÁGINA:\n" + problems.join("\n") : "OK  sem erros de página");
await browser.close();
