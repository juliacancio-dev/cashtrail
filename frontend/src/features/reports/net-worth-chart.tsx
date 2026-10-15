"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { NetWorthPoint } from "@/features/reports/schemas";
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
        <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
        <XAxis dataKey="month" tick={{ fill: "#898781", fontSize: 12 }} axisLine={{ stroke: "#c3c2b7" }} />
        <YAxis
          tick={{ fill: "#898781", fontSize: 12 }}
          axisLine={{ stroke: "#c3c2b7" }}
          tickFormatter={(value: number) => formatCurrency(value)}
          width={104}
        />
        <Tooltip formatter={(value) => formatCurrency(Number(value))} />
        <Legend />
        <Line type="monotone" dataKey="Ativos" stroke="#898781" strokeWidth={1.5} strokeDasharray="6 4" dot={false} />
        <Line type="monotone" dataKey="Passivos" stroke="#c2563a" strokeWidth={1.5} strokeDasharray="6 4" dot={false} />
        <Line type="monotone" dataKey="Patrimônio líquido" stroke="#2a78d6" strokeWidth={3} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
