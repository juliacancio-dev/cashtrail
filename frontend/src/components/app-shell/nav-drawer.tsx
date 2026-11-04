"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { LogOut, Search, X } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";

import { MODULES, isCurrent } from "./nav-config";

// Gaveta aberta pelo logo (doc 33, decisão 8): todas as telas agrupadas por módulo, com busca.

export type CloseReason = "dismiss" | "navigate";

const fold = (text: string) =>
  text
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function NavDrawer({
  open,
  focusSearch,
  pathname,
  onClose,
  onSignOut,
}: {
  open: boolean;
  focusSearch: boolean;
  pathname: string;
  onClose: (reason: CloseReason) => void;
  onSignOut: () => void;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const panelRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    // Espera a gaveta ficar interativa (sai do `inert`) antes de mover o foco.
    const timer = window.setTimeout(() => (focusSearch ? searchRef.current : closeRef.current)?.focus(), 30);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.clearTimeout(timer);
    };
  }, [open, focusSearch]);

  const term = fold(query.trim());
  const groups = MODULES.map((m) => ({
    module: m,
    tabs: m.tabs.filter((t) => !term || fold(t.label).includes(term) || fold(m.name).includes(term)),
  })).filter((g) => g.tabs.length > 0);
  const firstMatch = groups[0]?.tabs[0];

  function close(reason: CloseReason) {
    setQuery("");
    onClose(reason);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      close("dismiss");
      return;
    }
    if (event.key !== "Tab" || !panelRef.current) return;
    const items = Array.from(panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  // Cada item entra um pouco depois do anterior.
  let order = 0;
  const stagger = () => {
    const delay = open ? 80 + order++ * 18 : 0;
    return {
      className: `transition-[opacity,translate] duration-200 motion-reduce:transition-none ${open ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-2"}`,
      style: { transitionDelay: `${delay}ms` },
    };
  };

  const headRow = stagger();
  const searchRow = stagger();

  const linkClass = (current: boolean) =>
    `flex min-h-10 items-center gap-2.5 rounded-[9px] px-3 text-[15px] transition-colors focus-visible:outline-2 focus-visible:outline-nav-accent ${
      current
        ? "bg-nav-hover font-semibold text-nav-foreground shadow-[inset_3px_0_0_var(--nav-accent)]"
        : "text-nav-muted hover:bg-nav-hover hover:text-nav-foreground"
    }`;

  return (
    <>
      <div
        aria-hidden="true"
        onClick={() => close("dismiss")}
        className={`fixed inset-0 z-40 bg-black/30 transition-opacity duration-300 motion-reduce:transition-none dark:bg-black/50 ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />
      <div
        ref={panelRef}
        id="menu-geral"
        role="dialog"
        aria-modal="true"
        aria-label="Menu"
        inert={!open}
        aria-hidden={!open}
        onKeyDown={handleKeyDown}
        className={`fixed inset-y-2 left-2 z-50 flex w-[min(19rem,calc(100vw-2.5rem))] flex-col gap-3 overflow-y-auto rounded-[14px] border border-nav-edge bg-nav p-3 text-nav-foreground shadow-2xl transition-transform duration-300 ease-[cubic-bezier(.2,.8,.2,1)] motion-reduce:transition-none ${
          open ? "translate-x-0" : "-translate-x-[110%]"
        }`}
      >
        <div style={headRow.style} className={`${headRow.className} flex items-center justify-between pl-2`}>
          <span className="font-semibold">CashTrail</span>
          <button
            ref={closeRef}
            type="button"
            onClick={() => close("dismiss")}
            aria-label="Fechar menu"
            className="inline-flex size-10 items-center justify-center rounded-xl text-nav-muted hover:bg-nav-hover hover:text-nav-foreground focus-visible:outline-2 focus-visible:outline-nav-accent"
          >
            <X className="size-5" aria-hidden="true" />
          </button>
        </div>

        <label
          style={searchRow.style}
          className={`${searchRow.className} flex min-h-10 items-center gap-2 rounded-[10px] border border-transparent bg-nav-field px-3 text-nav-muted focus-within:border-nav-accent`}
        >
          <Search className="size-4 shrink-0" aria-hidden="true" />
          <span className="sr-only">Ir para uma tela</span>
          <input
            ref={searchRef}
            type="search"
            value={query}
            placeholder="Ir para uma tela"
            autoComplete="off"
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && firstMatch) {
                event.preventDefault();
                router.push(firstMatch.href);
                close("navigate");
              }
            }}
            className="min-w-0 flex-1 bg-transparent text-[15px] text-nav-foreground outline-none placeholder:text-nav-muted"
          />
          <kbd className="hidden rounded-[5px] border border-nav-hover px-1.5 font-mono text-[11px] md:inline">/</kbd>
        </label>

        <nav aria-label="Todas as telas" className="flex flex-col gap-2">
          {groups.length === 0 && <p className="px-3 text-[15px] text-nav-muted">Nenhuma tela com “{query.trim()}”.</p>}
          {groups.map(({ module: m, tabs }) => {
            const Icon = m.icon;
            if (m.tabs.length === 1) {
              const tab = tabs[0];
              const current = isCurrent(pathname, tab.href);
              const s = stagger();
              return (
                <Link
                  key={m.name}
                  href={tab.href}
                  onClick={() => close("navigate")}
                  aria-current={current ? "page" : undefined}
                  style={s.style}
                  className={`${s.className} ${linkClass(current)}`}
                >
                  <Icon className="size-4 shrink-0" aria-hidden="true" />
                  {tab.label}
                </Link>
              );
            }
            const head = stagger();
            return (
              <section key={m.name} aria-label={m.name} className="flex flex-col gap-0.5">
                <h2
                  style={head.style}
                  className={`${head.className} mb-0.5 flex items-center gap-2 rounded-[9px] bg-nav-section px-3 py-1.5 text-xs font-semibold tracking-[0.07em] text-white uppercase`}
                >
                  <Icon className="size-3.5 shrink-0 text-nav-accent" aria-hidden="true" />
                  {m.name}
                </h2>
                <ul className="flex flex-col gap-0.5">
                  {tabs.map((tab) => {
                    const current = isCurrent(pathname, tab.href);
                    const s = stagger();
                    return (
                      <li key={tab.href} style={s.style} className={s.className}>
                        <Link
                          href={tab.href}
                          onClick={() => close("navigate")}
                          aria-current={current ? "page" : undefined}
                          className={`${linkClass(current)} pl-3.5`}
                        >
                          {tab.label}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </nav>

        <div className="mt-auto flex items-center gap-1 border-t border-nav-hover pt-2.5">
          <ThemeToggle className="inline-flex size-10 items-center justify-center rounded-xl text-nav-muted hover:bg-nav-hover hover:text-nav-foreground focus-visible:outline-2 focus-visible:outline-nav-accent" />
          <button
            type="button"
            onClick={onSignOut}
            className="inline-flex min-h-10 items-center gap-2 rounded-xl px-3 text-[15px] text-nav-muted hover:bg-nav-hover hover:text-nav-foreground focus-visible:outline-2 focus-visible:outline-nav-accent"
          >
            <LogOut className="size-4" aria-hidden="true" />
            Sair
          </button>
        </div>
      </div>
    </>
  );
}
