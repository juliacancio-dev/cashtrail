"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SERIES_1, chartAxis, chartGrid, chartTooltip } from "@/lib/chart-theme";
import type { BalancePoint } from "@/features/dashboard/schemas";

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function BalanceEvolutionChart({ data }: { data: BalancePoint[] }) {
  if (data.length === 0) {
    return <p className="text-muted-foreground text-sm">Sem lançamentos no período.</p>;
  }

  const chartData = data.map((point) => ({ date: point.date, balance: Number(point.balance) }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ left: 8, right: 8 }}>
        <CartesianGrid {...chartGrid} />
        <XAxis dataKey="date" {...chartAxis} />
        <YAxis
          {...chartAxis}
          tickFormatter={(value: number) => formatCurrency(value)}
          width={80}
        />
        <Tooltip {...chartTooltip} formatter={(value) => formatCurrency(Number(value))} />
        <Line type="monotone" dataKey="balance" stroke={SERIES_1} strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
