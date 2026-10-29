"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CashFlowMonth } from "@/features/reports/schemas";
import { SERIES_1, chartAxis, chartGrid, chartTooltip } from "@/lib/chart-theme";
import { formatCurrency, monthLabel } from "@/lib/format";

/** Linha contínua = realizado, tracejada = projetado (mesma convenção do Conta Azul). */
export function CashFlowChart({ months }: { months: CashFlowMonth[] }) {
  const data = months.map((month) => ({
    month: monthLabel(month.month),
    realizado: month.closing_realized === null ? null : Number(month.closing_realized),
    projetado: Number(month.closing_projected),
  }));

  return (
    <div className="flex flex-col gap-2">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
          <CartesianGrid {...chartGrid} />
          <XAxis dataKey="month" {...chartAxis} />
          <YAxis
            {...chartAxis}
            tickFormatter={(value: number) => formatCurrency(value)}
            width={96}
          />
          <Tooltip {...chartTooltip} formatter={(value) => formatCurrency(Number(value))} />
          <Line
            type="monotone"
            dataKey="projetado"
            name="Projetado"
            stroke={SERIES_1}
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={{ r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="realizado"
            name="Realizado"
            stroke={SERIES_1}
            strokeWidth={3}
            dot={{ r: 4 }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-muted-foreground text-xs">
        Linha contínua: saldo realizado. Linha tracejada: saldo projetado (realizado + o que ainda está previsto).
      </p>
    </div>
  );
}
