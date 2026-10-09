"use client";

import Link from "next/link";

import type { CardsSummary } from "@/features/credit-cards/schemas";
import { formatCurrency } from "@/lib/format";

/** Alerta do dashboard (RF-030): faturas já fechadas que venceram ou vencem em breve. */
export function CardsAlert({ summary }: { summary: CardsSummary }) {
  if (summary.overdue_count === 0 && summary.due_soon_count === 0) return null;

  return (
    <Link
      href="/cards"
      className={`rounded-lg border p-4 text-sm ${
        summary.overdue_count > 0 ? "border-destructive/40 bg-destructive/5" : "border-amber-500/40 bg-amber-500/5"
      }`}
    >
      <p className="font-medium">
        {summary.overdue_count > 0 && `${summary.overdue_count} fatura(s) de cartão vencida(s)`}
        {summary.overdue_count > 0 && summary.due_soon_count > 0 && " · "}
        {summary.due_soon_count > 0 && `${summary.due_soon_count} vence(m) em ${summary.days} dias`}
      </p>
      <p className="text-muted-foreground">
        Vencido: {formatCurrency(summary.overdue_amount)} · A vencer: {formatCurrency(summary.due_soon_amount)}. Ver cartões.
      </p>
    </Link>
  );
}
