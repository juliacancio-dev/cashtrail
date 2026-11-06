"use client";

import Link from "next/link";

import type { CommitmentSummary } from "@/features/commitments/schemas";
import type { CardsSummary } from "@/features/credit-cards/schemas";
import type { DebtsSummary } from "@/features/debts/schemas";
import type { CategorySpending, DashboardSummary } from "@/features/dashboard/schemas";
import type { InsuranceSummary } from "@/features/insurance/schemas";
import type { NetWorthPoint } from "@/features/reports/schemas";
import { formatCurrency, formatDate, monthName } from "@/lib/format";
import { SERIES_1 } from "@/lib/chart-theme";

// Resumo do mês no estilo do calendário (doc 33, decisões 1 e 2): um número, uma frase, os avisos numa
// lista só, o gasto por categoria em ordem e o patrimônio numa linha.

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

export function MonthHero({ summary, month, isCurrent }: { summary: DashboardSummary; month: string; isCurrent: boolean }) {
  const balance = Number(summary.balance);
  const income = Number(summary.income_total);
  const expense = Number(summary.expense_total);
  const name = monthName(month);
  const soFar = isCurrent ? " até agora" : "";
  const empty = income === 0 && expense === 0;

  return (
    <section aria-label="Resultado do mês" className="flex flex-col gap-2">
      <p className={`font-mono text-4xl font-medium tracking-tight sm:text-5xl ${balance < 0 ? "text-expense" : ""}`}>
        {balance < 0 ? "− " : ""}
        {formatCurrency(Math.abs(balance))}
      </p>
      <p className="text-muted-foreground max-w-[62ch] text-base">
        {empty ? (
          `Nenhum lançamento em ${name}${soFar}.`
        ) : (
          <>
            {balance >= 0 ? `sobraram em ${name}${soFar}.` : `saiu mais do que entrou em ${name}${soFar}.`} Entraram{" "}
            <strong className="text-foreground font-mono font-semibold">{formatCurrency(income)}</strong> e saíram{" "}
            <strong className="text-foreground font-mono font-semibold">{formatCurrency(expense)}</strong>.
          </>
        )}
      </p>
    </section>
  );
}

type Severity = "critical" | "warning" | "info";
type Notice = { key: string; severity: Severity; text: string; amount?: number; href: string };

const dotClass: Record<Severity, string> = { critical: "bg-expense", warning: "bg-warning", info: "bg-info" };
const severityLabel: Record<Severity, string> = { critical: "Atrasado", warning: "Em breve", info: "Informação" };

/** Junta os avisos de contas, cartões, dívidas e seguros numa lista só, o mais grave primeiro. */
export function buildNotices({
  commitments,
  cards,
  debts,
  insurance,
}: {
  commitments: CommitmentSummary | null;
  cards: CardsSummary | null;
  debts: DebtsSummary | null;
  insurance: InsuranceSummary | null;
}): Notice[] {
  const notices: Notice[] = [];

  if (commitments) {
    const overdue = commitments.payable.overdue_count + commitments.receivable.overdue_count;
    const soon = commitments.payable.due_soon_count + commitments.receivable.due_soon_count;
    if (overdue > 0 || soon > 0) {
      const parts = [];
      if (overdue > 0) parts.push(plural(overdue, "conta atrasada", "contas atrasadas"));
      if (soon > 0) parts.push(`${soon} ${soon === 1 ? "vence" : "vencem"} nos próximos ${commitments.days} dias`);
      const toPay = Number(commitments.payable.overdue_amount) + Number(commitments.payable.due_soon_amount);
      notices.push({ key: "commitments", severity: overdue > 0 ? "critical" : "warning", text: parts.join(" e "), amount: toPay || undefined, href: "/commitments" });
    }
  }

  if (cards && (cards.overdue_count > 0 || cards.due_soon_count > 0)) {
    const overdue = cards.overdue_count > 0;
    notices.push({
      key: "cards",
      severity: overdue ? "critical" : "warning",
      text: overdue
        ? plural(cards.overdue_count, "fatura de cartão vencida", "faturas de cartão vencidas")
        : `${plural(cards.due_soon_count, "fatura de cartão vence", "faturas de cartão vencem")} nos próximos ${cards.days} dias`,
      amount: Number(overdue ? cards.overdue_amount : cards.due_soon_amount),
      href: "/cards",
    });
  }

  if (insurance) {
    const overdue = insurance.overdue_renewals.length;
    const soon = insurance.renewals_soon.length;
    if (overdue > 0 || soon > 0) {
      const names = [...insurance.overdue_renewals, ...insurance.renewals_soon].map((p) => `${p.name} (${formatDate(p.renews_on)})`).join(", ");
      notices.push({
        key: "insurance",
        severity: overdue > 0 ? "critical" : "warning",
        text: `${overdue > 0 ? plural(overdue, "seguro com renovação vencida", "seguros com renovação vencida") : plural(soon, "seguro renova", "seguros renovam") + " em até 30 dias"}: ${names}`,
        href: "/insurance",
      });
    }
  }

  if (debts && debts.active_count > 0) {
    const next = debts.next_due_date ? ` · próxima parcela em ${formatDate(debts.next_due_date)}` : "";
    notices.push({
      key: "debts",
      severity: debts.overdue_count > 0 ? "critical" : "info",
      text:
        debts.overdue_count > 0
          ? `${plural(debts.overdue_count, "dívida com parcela atrasada", "dívidas com parcela atrasada")}${next}`
          : `Saldo devedor em ${plural(debts.active_count, "dívida", "dívidas")}${next}`,
      amount: Number(debts.outstanding_total),
      href: "/debts",
    });
  }

  const order: Record<Severity, number> = { critical: 0, warning: 1, info: 2 };
  return notices.sort((a, b) => order[a.severity] - order[b.severity]);
}

export function AttentionList({ notices }: { notices: Notice[] }) {
  if (notices.length === 0) return null;
  return (
    <section aria-labelledby="atencao" className="flex flex-col gap-2">
      <h2 id="atencao" className="text-muted-foreground text-[13px] font-medium tracking-[0.06em] uppercase">
        Atenção
      </h2>
      <ul className="border-border border-t">
        {notices.map((n) => (
          <li key={n.key} className="border-border border-b">
            <Link href={n.href} className="hover:bg-muted flex min-h-12 items-center justify-between gap-4 py-2.5 transition-colors">
              <span className="flex min-w-0 items-baseline gap-2.5">
                <span aria-hidden="true" className={`size-[7px] shrink-0 translate-y-[-1px] rounded-full ${dotClass[n.severity]}`} />
                <span className="sr-only">{severityLabel[n.severity]}: </span>
                <span>{n.text}</span>
              </span>
              <span className="text-muted-foreground shrink-0 font-mono">
                {n.amount !== undefined && <span className="text-foreground">{formatCurrency(n.amount)} </span>}
                <span aria-hidden="true">→</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

const MAX_CATEGORIES = 8;

/** Barras horizontais numa cor só (categorias são uma série), do maior para o menor, com o valor escrito. */
export function CategoryBars({ data }: { data: CategorySpending[] }) {
  const sorted = data.map((c) => ({ name: c.category_name || "Sem categoria", total: Number(c.total) })).sort((a, b) => b.total - a.total);
  const rows =
    sorted.length > MAX_CATEGORIES
      ? [...sorted.slice(0, MAX_CATEGORIES - 1), { name: `Outras (${sorted.length - MAX_CATEGORIES + 1})`, total: sorted.slice(MAX_CATEGORIES - 1).reduce((s, c) => s + c.total, 0) }]
      : sorted;
  const max = rows[0]?.total ?? 0;

  return (
    <section aria-labelledby="por-categoria" className="flex flex-col gap-3">
      <h2 id="por-categoria" className="text-muted-foreground text-[13px] font-medium tracking-[0.06em] uppercase">
        Gasto por categoria
      </h2>
      {rows.length === 0 ? (
        <p className="text-muted-foreground text-sm">Sem despesas no mês.</p>
      ) : (
        <ul className="grid grid-cols-[minmax(5.5rem,9rem)_1fr_auto] items-center gap-x-3.5 gap-y-2.5">
          {rows.map((r) => (
            <li key={r.name} className="contents" title={`${r.name}: ${formatCurrency(r.total)}`}>
              <span className="truncate text-[15px]">{r.name}</span>
              <span aria-hidden="true" className="bg-muted h-2.5 rounded-[4px]">
                <span
                  data-bar
                  className="block h-full rounded-[4px]"
                  style={{ width: `${max ? Math.max((r.total / max) * 100, 1.5) : 0}%`, background: SERIES_1 }}
                />
              </span>
              <span className="text-right font-mono text-sm">{formatCurrency(r.total)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Patrimônio líquido de hoje e a variação desde o fim do mês passado, numa linha que leva ao Balanço. */
export function NetWorthLine({ points }: { points: NetWorthPoint[] }) {
  const current = points[points.length - 1];
  if (!current) return null;
  const previous = points.length > 1 ? points[points.length - 2] : null;
  const change = previous ? Number(current.net_worth) - Number(previous.net_worth) : null;

  return (
    <Link href="/net-worth" className="border-border hover:bg-muted flex min-h-14 items-center justify-between gap-4 border-y py-2.5 transition-colors">
      <span className="flex flex-col">
        <span>Patrimônio líquido</span>
        {change !== null && previous && (
          <span className="text-muted-foreground text-[13px]">
            {change >= 0 ? "+ " : "− "}
            {formatCurrency(Math.abs(change))} desde o fim de {monthName(previous.month)}
          </span>
        )}
      </span>
      <span className={`shrink-0 font-mono ${Number(current.net_worth) < 0 ? "text-expense" : ""}`}>
        {formatCurrency(current.net_worth)} <span className="text-muted-foreground" aria-hidden="true">→</span>
      </span>
    </Link>
  );
}
