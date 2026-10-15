"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/accounts", label: "Contas" },
  { href: "/categories", label: "Categorias" },
  { href: "/transactions", label: "Lançamentos" },
  { href: "/commitments", label: "A pagar/receber" },
  { href: "/cards", label: "Cartões" },
  { href: "/transfers", label: "Transferências" },
  { href: "/debts", label: "Dívidas" },
  { href: "/assets", label: "Bens" },
  { href: "/investments", label: "Investimentos" },
  { href: "/net-worth", label: "Patrimônio" },
  { href: "/tax", label: "Imposto de renda" },
  { href: "/dre", label: "DRE" },
  { href: "/cash-flow", label: "Fluxo de caixa" },
  { href: "/import", label: "Importar" },
  { href: "/budgets", label: "Orçamentos" },
  { href: "/goals", label: "Metas" },
  { href: "/recurring", label: "Recorrências" },
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={
            pathname === link.href
              ? "font-medium underline"
              : "text-muted-foreground hover:text-foreground"
          }
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
