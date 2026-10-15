"use client";

import Link from "next/link";

import type { NetWorthPoint } from "@/features/reports/schemas";
import { formatCurrency } from "@/lib/format";

/** Dashboard (RF-048): patrimônio líquido de hoje e a variação contra o fim do mês anterior. */
export function NetWorthCard({ points }: { points: NetWorthPoint[] }) {
  const current = points[points.length - 1];
  if (!current) return null;
  const previous = points.length > 1 ? points[points.length - 2] : null;
  const change = previous ? Number(current.net_worth) - Number(previous.net_worth) : null;

  return (
    <Link href="/net-worth" className="rounded-lg border p-4 text-sm">
      <p className="text-muted-foreground">Patrimônio líquido</p>
      <p className={`text-xl font-semibold ${Number(current.net_worth) < 0 ? "text-destructive" : ""}`}>
        {formatCurrency(current.net_worth)}
      </p>
      {change !== null && (
        <p className="text-muted-foreground">
          {change >= 0 ? "+ " : "− "}
          {formatCurrency(Math.abs(change))} desde o fim do mês passado. Ver patrimônio.
        </p>
      )}
    </Link>
  );
}
