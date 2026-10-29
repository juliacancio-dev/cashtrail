"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategorySpending } from "@/features/dashboard/schemas";
import { SERIES_1, chartAxis, chartGrid, chartTooltip } from "@/lib/chart-theme";

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
        <CartesianGrid {...chartGrid} />
        <XAxis dataKey="name" {...chartAxis} />
        <YAxis
          {...chartAxis}
          tickFormatter={(value: number) => formatCurrency(value)}
          width={80}
        />
        <Tooltip {...chartTooltip} formatter={(value) => formatCurrency(Number(value))} />
        {/* Categorias são uma série só: o nome já está no eixo, então todas as barras têm a mesma cor. */}
        <Bar dataKey="total" name="Gasto" fill={SERIES_1} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
