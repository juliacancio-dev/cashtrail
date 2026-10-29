// Cores dos gráficos (Recharts) lidas dos tokens do tema, para seguirem o claro e o escuro
// (doc 32, etapa 5). Grade e eixos recessivos; texto dos eixos no tom apagado do app.

export const chartGrid = { stroke: "var(--chart-grid)", strokeDasharray: "3 3", vertical: false } as const;

export const chartAxis = {
  tick: { fill: "var(--muted-foreground)", fontSize: 12 },
  axisLine: { stroke: "var(--chart-axis)" },
  tickLine: { stroke: "var(--chart-axis)" },
} as const;

export const chartTooltip = {
  contentStyle: {
    background: "var(--popover)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    color: "var(--popover-foreground)",
  },
  labelStyle: { color: "var(--popover-foreground)" },
  itemStyle: { color: "var(--popover-foreground)" },
  cursor: { stroke: "var(--chart-axis)", fill: "var(--muted)" },
} as const;

/** Série única ou primeira série: azul da paleta validada. */
export const SERIES_1 = "var(--chart-1)";
