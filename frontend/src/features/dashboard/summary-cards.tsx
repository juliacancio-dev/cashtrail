"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { DashboardSummary } from "@/features/dashboard/schemas";

function formatCurrency(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function SummaryCards({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <Card>
        <CardContent className="py-4">
          <p className="text-muted-foreground text-sm">Receitas</p>
          <p className="text-xl font-semibold text-green-600">{formatCurrency(summary.income_total)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="py-4">
          <p className="text-muted-foreground text-sm">Despesas</p>
          <p className="text-destructive text-xl font-semibold">{formatCurrency(summary.expense_total)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="py-4">
          <p className="text-muted-foreground text-sm">Saldo do período</p>
          <p className="text-xl font-semibold">{formatCurrency(summary.balance)}</p>
        </CardContent>
      </Card>
    </div>
  );
}
