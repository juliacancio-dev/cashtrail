"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-context";

import { MODULES, isCurrent, moduleFor } from "./nav-config";

const linkBase = "inline-flex min-h-11 items-center rounded-full px-3 text-[15px] transition-colors";

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  // Antes de confirmar a sessão a página só mostra "Carregando..."; o menu aparece depois.
  if (!user) return null;

  const active = moduleFor(pathname);
  const signOut = () => logout().then(() => router.push("/login"));

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex w-full max-w-5xl items-center gap-2 px-6 py-3">
        <Link href="/dashboard" className="mr-auto text-[17px] font-semibold">
          CashTrail
        </Link>
        <nav aria-label="Módulos" className="hidden items-center gap-1 md:flex">
          {MODULES.map((m) => (
            <Link
              key={m.name}
              href={m.tabs[0].href}
              aria-current={m === active ? "true" : undefined}
              className={`${linkBase} ${m === active ? "font-medium text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >
              {m.name}
            </Link>
          ))}
        </nav>
        <ThemeToggle />
        <Button variant="outline" className="hidden min-h-11 md:inline-flex" onClick={signOut}>
          Sair
        </Button>
        <Button
          variant="outline"
          className="min-h-11 md:hidden"
          aria-expanded={menuOpen}
          aria-controls="menu-celular"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? "Fechar" : "Menu"}
        </Button>
      </div>

      {menuOpen && (
        <nav id="menu-celular" aria-label="Módulos" className="border-t border-border px-6 py-2 md:hidden">
          {MODULES.map((m) => (
            <div key={m.name} className="border-b border-border py-3 last:border-b-0">
              <p className="text-lg font-medium">{m.name}</p>
              <ul className="mt-1 flex flex-col">
                {m.tabs.map((t) => (
                  <li key={t.href}>
                    <Link
                      href={t.href}
                      onClick={() => setMenuOpen(false)}
                      aria-current={isCurrent(pathname, t.href) ? "page" : undefined}
                      className={`flex min-h-11 items-center ${isCurrent(pathname, t.href) ? "font-medium text-foreground" : "text-muted-foreground"}`}
                    >
                      {t.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <Button variant="outline" className="my-3 min-h-11 w-full" onClick={signOut}>
            Sair
          </Button>
        </nav>
      )}

      {active && (
        <nav aria-label={`Telas de ${active.name}`} className="mx-auto w-full max-w-5xl overflow-x-auto px-6">
          <ul className="flex min-w-max gap-1">
            {active.tabs.map((t) => {
              const current = isCurrent(pathname, t.href);
              return (
                <li key={t.href}>
                  <Link
                    href={t.href}
                    aria-current={current ? "page" : undefined}
                    className={`-mb-px inline-flex min-h-11 items-center border-b-2 px-3 text-[15px] whitespace-nowrap ${current ? "border-foreground font-medium text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
                  >
                    {t.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      )}
    </header>
  );
}
