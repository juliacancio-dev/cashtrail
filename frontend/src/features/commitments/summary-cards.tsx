"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { CommitmentSummary, DirectionSummary } from "@/features/commitments/schemas";
import { formatCurrency } from "@/lib/format";

function SummaryCard({ title, data, days }: { title: string; data: DirectionSummary; days: number }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 py-4">
        <p className="text-muted-foreground text-sm">{title}</p>
        <p className="text-xl font-semibold">{formatCurrency(data.open_amount)}</p>
        <p className={data.overdue_count > 0 ? "text-destructive text-sm font-medium" : "text-muted-foreground text-sm"}>
          {data.overdue_count > 0
            ? `${data.overdue_count} atrasado(s) · ${formatCurrency(data.overdue_amount)}`
            : "Nada atrasado"}
        </p>
        <p className="text-muted-foreground text-sm">
          {data.due_soon_count > 0
            ? `${data.due_soon_count} vence(m) em ${days} dias · ${formatCurrency(data.due_soon_amount)}`
            : `Nada vence nos próximos ${days} dias`}
        </p>
      </CardContent>
    </Card>
  );
}

export function CommitmentSummaryCards({ summary }: { summary: CommitmentSummary }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <SummaryCard title="A pagar (em aberto)" data={summary.payable} days={summary.days} />
      <SummaryCard title="A receber (em aberto)" data={summary.receivable} days={summary.days} />
    </div>
  );
}
