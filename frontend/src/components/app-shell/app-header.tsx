"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { LogOut } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/features/auth/auth-context";

import { MODULES, isCurrent, moduleFor } from "./nav-config";
import { NavDrawer, type CloseReason } from "./nav-drawer";

// Cápsula flutuante com os módulos e, embaixo, as telas do módulo atual (doc 33, decisão 8).
// O logo abre a gaveta com todas as telas.

const capButton =
  "inline-flex size-10 items-center justify-center rounded-xl text-nav-muted transition-colors hover:bg-nav-hover hover:text-nav-foreground focus-visible:outline-2 focus-visible:outline-nav-accent";

function isTyping(target: EventTarget | null) {
  const el = target as HTMLElement | null;
  return !!el && (el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName));
}

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [menu, setMenu] = useState<{ open: boolean; search: boolean }>({ open: false, search: false });
  const logoRef = useRef<HTMLButtonElement>(null);

  // "/" abre a gaveta já na busca, de qualquer tela (menos quando se está digitando).
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || isTyping(event.target)) return;
      event.preventDefault();
      setMenu({ open: true, search: true });
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Antes de confirmar a sessão a página só mostra "Carregando..."; o menu aparece depois.
  if (!user) return null;

  const active = moduleFor(pathname);
  const signOut = () => logout().then(() => router.push("/login"));

  function closeMenu(reason: CloseReason) {
    setMenu({ open: false, search: false });
    if (reason === "dismiss") logoRef.current?.focus();
  }

  return (
    <header className="relative z-30">
      <div className="mx-auto w-full max-w-5xl px-3 pt-3.5 sm:px-4">
        <div className="flex h-14 items-center gap-1 rounded-[14px] border border-nav-edge bg-nav pr-2 pl-1.5 text-nav-foreground shadow-[0_2px_8px_rgba(0,0,0,0.08)]">
          <button
            ref={logoRef}
            type="button"
            onClick={() => setMenu({ open: true, search: false })}
            aria-label="Abrir menu"
            aria-expanded={menu.open}
            aria-controls="menu-geral"
            className="group relative mr-1 inline-flex min-h-11 shrink-0 items-center gap-2.5 rounded-xl py-1.5 pr-3 pl-1.5 font-semibold transition-colors hover:bg-nav-hover focus-visible:outline-2 focus-visible:outline-nav-accent sm:mr-2"
          >
            <span className="relative grid size-8 place-items-center rounded-[9px] bg-nav-accent text-sm font-bold text-nav-accent-foreground">
              C
              <span aria-hidden="true" className="nav-ping pointer-events-none absolute -inset-1 rounded-xl border-2 border-nav-accent" />
            </span>
            {/* Três tracinhos: avisam que o logo é um menu; viram X com a gaveta aberta. */}
            <span aria-hidden="true" className="flex w-3.5 flex-col gap-[3px]">
              {["w-3.5", "w-2.5", "w-1.5"].map((width, i) => (
                <i
                  key={width}
                  className={`block h-0.5 rounded-full transition-[width,transform,opacity,background-color] duration-200 motion-reduce:transition-none ${
                    menu.open
                      ? `w-3.5 bg-nav-foreground ${i === 0 ? "translate-y-[5px] rotate-45" : i === 1 ? "opacity-0" : "-translate-y-[5px] -rotate-45"}`
                      : `${width} bg-nav-muted group-hover:w-3.5 group-hover:bg-nav-foreground`
                  }`}
                />
              ))}
            </span>
            <span className="hidden sm:inline">CashTrail</span>
            <span
              aria-hidden="true"
              className="pointer-events-none absolute top-[calc(100%+10px)] left-1.5 rounded-md bg-foreground px-2 py-0.5 text-xs font-medium whitespace-nowrap text-background opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
            >
              Menu
            </span>
          </button>

          <nav aria-label="Módulos" className="flex min-w-0 gap-0.5 overflow-hidden">
            {MODULES.map((m) => {
              const current = m === active;
              return (
                <Link
                  key={m.name}
                  href={m.tabs[0].href}
                  aria-current={current ? "true" : undefined}
                  className={`min-h-10 items-center rounded-full px-3 text-[15px] whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-nav-accent ${
                    current
                      ? "inline-flex bg-nav-accent font-semibold text-nav-accent-foreground"
                      : "hidden text-nav-muted hover:bg-nav-hover hover:text-nav-foreground md:inline-flex"
                  }`}
                >
                  {m.name}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex shrink-0 items-center gap-0.5">
            <ThemeToggle className={capButton} />
            {/* No celular o Sair fica só na gaveta. */}
            <button
              type="button"
              onClick={signOut}
              className="hidden min-h-10 items-center gap-2 rounded-xl px-3 text-[15px] text-nav-muted transition-colors hover:bg-nav-hover hover:text-nav-foreground focus-visible:outline-2 focus-visible:outline-nav-accent md:inline-flex"
            >
              Sair
              <LogOut className="size-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      {active && active.tabs.length > 1 && (
        <nav aria-label={`Telas de ${active.name}`} className="mx-auto w-full max-w-5xl overflow-x-auto px-6 pt-2">
          <ul className="flex min-w-max gap-5">
            {active.tabs.map((t) => {
              const current = isCurrent(pathname, t.href);
              return (
                <li key={t.href}>
                  <Link
                    href={t.href}
                    aria-current={current ? "page" : undefined}
                    className={`inline-flex min-h-11 items-center border-b-2 text-[15px] whitespace-nowrap ${
                      current
                        ? "border-accent-money font-semibold text-foreground"
                        : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {t.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      )}

      <NavDrawer open={menu.open} focusSearch={menu.search} pathname={pathname} onClose={closeMenu} onSignOut={signOut} />
    </header>
  );
}
