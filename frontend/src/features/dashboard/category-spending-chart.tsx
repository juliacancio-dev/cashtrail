"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategorySpending } from "@/features/dashboard/schemas";

// Paleta categórica validada (skill dataviz/references/palette.md) — ordem fixa, nunca ciclada.
const CATEGORY_COLORS = [
  "#2a78d6",
  "#eb6834",
  "#1baf7a",
  "#eda100",
  "#e87ba4",
  "#008300",
  "#4a3aa7",
  "#e34948",
];

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function CategorySpendingChart({ data }: { data: CategorySpending[] }) {
  if (data.length === 0) {
    return <p className="text-muted-foreground text-sm">Sem despesas no período.</p>;
  }

  const chartData = data.map((item) => ({ name: item.category_name, total: Number(item.total) }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} margin={{ left: 8, right: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#898781", fontSize: 12 }} axisLine={{ stroke: "#c3c2b7" }} />
        <YAxis
          tick={{ fill: "#898781", fontSize: 12 }}
          axisLine={{ stroke: "#c3c2b7" }}
          tickFormatter={(value: number) => formatCurrency(value)}
          width={80}
        />
        <Tooltip formatter={(value) => formatCurrency(Number(value))} />
        <Bar dataKey="total" radius={[4, 4, 0, 0]}>
          {chartData.map((_, index) => (
            <Cell key={index} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
