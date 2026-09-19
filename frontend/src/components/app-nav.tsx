"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/accounts", label: "Contas" },
  { href: "/categories", label: "Categorias" },
  { href: "/transactions", label: "Lançamentos" },
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-4 text-sm">
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
