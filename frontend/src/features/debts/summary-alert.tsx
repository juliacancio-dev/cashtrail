"use client";

import Link from "next/link";

import type { DebtsSummary } from "@/features/debts/schemas";
import { formatCurrency, formatDate } from "@/lib/format";

/** Dashboard (RF-039): saldo devedor das dívidas e a próxima parcela. Some se não há dívida ativa. */
export function DebtsAlert({ summary }: { summary: DebtsSummary }) {
  if (summary.active_count === 0) return null;

  return (
    <Link
      href="/debts"
      className={`rounded-lg border p-4 text-sm ${
        summary.overdue_count > 0 ? "border-destructive/40 bg-destructive/5" : ""
      }`}
    >
      <p className="font-medium">
        Dívidas: saldo devedor {formatCurrency(summary.outstanding_total)} em {summary.active_count} dívida(s)
        {summary.overdue_count > 0 && ` · ${summary.overdue_count} com parcela atrasada`}
      </p>
      {summary.next_due_date && (
        <p className="text-muted-foreground">
          Próxima parcela: {summary.next_debt_name} {formatCurrency(summary.next_amount ?? 0)} em{" "}
          {formatDate(summary.next_due_date)}. Ver dívidas.
        </p>
      )}
    </Link>
  );
}
