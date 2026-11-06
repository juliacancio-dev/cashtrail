"use client";

import type { Transaction } from "@/features/transactions/schemas";
import { formatCurrency, todayIso } from "@/lib/format";

// Lançamentos do mês agrupados por dia, do mais recente para o mais antigo (doc 33, decisão 3).

type Option = { id: string; name: string };

const WEEKDAYS = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];
const MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

/** "2026-11-04" -> "quarta, 4 de novembro", sem passar por fuso. */
function dayTitle(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const weekday = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
  return `${WEEKDAYS[weekday]}, ${d} de ${MONTHS[m - 1]}`;
}

function yesterdayIso(): string {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const signed = (value: number) => `${value < 0 ? "−" : "+"} ${formatCurrency(Math.abs(value))}`;
const valueOf = (t: Transaction) => (t.type === "expense" ? -Number(t.amount) : Number(t.amount));

export function TransactionList({
  transactions,
  accounts,
  categories,
}: {
  transactions: Transaction[];
  accounts: Option[];
  categories: Option[];
}) {
  if (transactions.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhum lançamento neste mês.</p>;
  }

  const accountName = (id: string) => accounts.find((a) => a.id === id)?.name ?? "-";
  const categoryName = (id: string) => categories.find((c) => c.id === id)?.name ?? "-";
  const today = todayIso();
  const yesterday = yesterdayIso();

  const days = new Map<string, Transaction[]>();
  [...transactions]
    .sort((a, b) => b.occurred_at.localeCompare(a.occurred_at) || b.created_at.localeCompare(a.created_at))
    .forEach((t) => days.set(t.occurred_at, [...(days.get(t.occurred_at) ?? []), t]));

  return (
    <div className="flex flex-col gap-5">
      {[...days.entries()].map(([day, items]) => {
        const total = items.reduce((sum, t) => sum + valueOf(t), 0);
        const label = day === today ? " · hoje" : day === yesterday ? " · ontem" : "";
        return (
          <section key={day} aria-label={`${dayTitle(day)}${label}`}>
            <h2 className="text-muted-foreground flex items-baseline justify-between gap-4 pb-1.5 text-sm font-normal">
              <span>
                {dayTitle(day)}
                {label}
              </span>
              <span className="font-mono text-[13px]">
                <span className="sr-only">total do dia </span>
                {signed(total)}
              </span>
            </h2>
            <ul className="border-border border-t">
              {items.map((t) => (
                <li key={t.id} className="border-border flex items-center justify-between gap-4 border-b py-2.5">
                  <div className="min-w-0">
                    <p className="truncate">{t.description || categoryName(t.category_id)}</p>
                    <p className="text-muted-foreground truncate text-[13px]">
                      {categoryName(t.category_id)} · {accountName(t.account_id)}
                    </p>
                  </div>
                  <p className={`shrink-0 font-mono ${t.type === "expense" ? "text-expense" : "text-income"}`}>{signed(valueOf(t))}</p>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
