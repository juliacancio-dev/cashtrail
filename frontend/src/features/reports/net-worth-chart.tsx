"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { NetWorthPoint } from "@/features/reports/schemas";
import { SERIES_1, chartAxis, chartGrid, chartTooltip } from "@/lib/chart-theme";
import { formatCurrency, monthLabel } from "@/lib/format";

/** Patrimônio líquido (linha forte) com ativos e passivos como contexto. */
export function NetWorthChart({ points }: { points: NetWorthPoint[] }) {
  const data = points.map((point) => ({
    month: monthLabel(point.month),
    "Patrimônio líquido": Number(point.net_worth),
    Ativos: Number(point.total_assets),
    Passivos: Number(point.total_liabilities),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
        <CartesianGrid {...chartGrid} />
        <XAxis dataKey="month" {...chartAxis} />
        <YAxis
          {...chartAxis}
          tickFormatter={(value: number) => formatCurrency(value)}
          width={104}
        />
        <Tooltip {...chartTooltip} formatter={(value) => formatCurrency(Number(value))} />
        <Legend formatter={(value) => <span style={{ color: "var(--muted-foreground)" }}>{value}</span>} />
        <Line type="monotone" dataKey="Ativos" stroke="var(--muted-foreground)" strokeWidth={1.5} strokeDasharray="6 4" dot={false} />
        <Line type="monotone" dataKey="Passivos" stroke="var(--chart-8)" strokeWidth={1.5} strokeDasharray="6 4" dot={false} />
        <Line type="monotone" dataKey="Patrimônio líquido" stroke={SERIES_1} strokeWidth={3} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
