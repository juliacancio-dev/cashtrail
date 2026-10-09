"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CashFlowMonth } from "@/features/reports/schemas";
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
          <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
          <XAxis dataKey="month" tick={{ fill: "#898781", fontSize: 12 }} axisLine={{ stroke: "#c3c2b7" }} />
          <YAxis
            tick={{ fill: "#898781", fontSize: 12 }}
            axisLine={{ stroke: "#c3c2b7" }}
            tickFormatter={(value: number) => formatCurrency(value)}
            width={96}
          />
          <Tooltip formatter={(value) => formatCurrency(Number(value))} />
          <Line
            type="monotone"
            dataKey="projetado"
            name="Projetado"
            stroke="#2a78d6"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={{ r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="realizado"
            name="Realizado"
            stroke="#2a78d6"
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
