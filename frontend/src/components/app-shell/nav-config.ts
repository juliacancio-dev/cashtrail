// Módulos do menu e as telas de cada um (doc 32, decisão 2). O link do módulo leva à primeira tela.
export type NavTab = { href: string; label: string };
export type NavModule = { name: string; tabs: NavTab[] };

export const MODULES: NavModule[] = [
  {
    name: "Caixa",
    tabs: [
      { href: "/dashboard", label: "Resumo do mês" },
      { href: "/transactions", label: "Lançamentos" },
      { href: "/categories", label: "Categorias" },
      { href: "/transfers", label: "Transferências" },
      { href: "/import", label: "Importar extrato" },
    ],
  },
  {
    name: "Compromissos",
    tabs: [
      { href: "/commitments", label: "A pagar e a receber" },
      { href: "/cards", label: "Cartões e faturas" },
      { href: "/recurring", label: "Recorrências" },
      { href: "/debts", label: "Dívidas" },
    ],
  },
  {
    name: "Patrimônio",
    tabs: [
      { href: "/accounts", label: "Contas" },
      { href: "/assets", label: "Bens" },
      { href: "/investments", label: "Investimentos" },
      { href: "/net-worth", label: "Balanço" },
    ],
  },
  {
    name: "Planejamento",
    tabs: [
      { href: "/budgets", label: "Orçamentos" },
      { href: "/goals", label: "Metas" },
      { href: "/retirement", label: "Independência" },
      { href: "/insurance", label: "Seguros" },
    ],
  },
  {
    name: "Relatórios",
    tabs: [
      { href: "/dre", label: "DRE" },
      { href: "/cash-flow", label: "Fluxo de caixa" },
      { href: "/tax", label: "Imposto de renda" },
    ],
  },
];

const normalize = (path: string) => (path.length > 1 ? path.replace(/\/+$/, "") : path);

export function moduleFor(pathname: string): NavModule | undefined {
  const path = normalize(pathname);
  return MODULES.find((m) => m.tabs.some((t) => t.href === path));
}

export function isCurrent(pathname: string, href: string): boolean {
  return normalize(pathname) === href;
}
