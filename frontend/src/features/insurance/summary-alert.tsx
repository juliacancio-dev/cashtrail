"use client";

import Link from "next/link";

import type { InsuranceSummary } from "@/features/insurance/schemas";
import { formatDate } from "@/lib/format";

/** Dashboard (RF-075): renovações vencidas ou em até 30 dias e bens sem apólice. Some quando não há nada a avisar. */
export function InsuranceAlert({ summary }: { summary: InsuranceSummary }) {
  const overdue = summary.overdue_renewals;
  const soon = summary.renewals_soon;
  if (overdue.length === 0 && soon.length === 0) return null;

  return (
    <Link
      href="/insurance"
      className={`rounded-lg border p-4 text-sm ${
        overdue.length > 0 ? "border-destructive/40 bg-destructive/5" : "border-amber-500/40 bg-amber-500/5"
      }`}
    >
      <p className="font-medium">
        {overdue.length > 0 && `${overdue.length} renovação(ões) de seguro vencida(s)`}
        {overdue.length > 0 && soon.length > 0 && " · "}
        {soon.length > 0 && `${soon.length} renova(m) em até 30 dias`}
      </p>
      <p className="text-muted-foreground">
        {[...overdue, ...soon].map((p) => `${p.name} (${formatDate(p.renews_on)})`).join(", ")}. Ver seguros.
      </p>
    </Link>
  );
}
