"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-context";
import { CashFlowChart } from "@/features/reports/cash-flow-chart";
import { cashFlowCsvPath, downloadCsv, getCashFlow, getCashFlowItems } from "@/features/reports/api";
import {
  sourceLabels,
  type CashFlow,
  type CashFlowMonth,
  type FlowColumn,
  type FlowDirection,
  type FlowItem,
} from "@/features/reports/schemas";
import { currentMonthIso, formatCurrency, formatDate, monthLabel } from "@/lib/format";

type Selection = { month: string; column: FlowColumn; direction: FlowDirection };

const statusLabel: Record<CashFlowMonth["status"], string> = {
  past: "passado",
  current: "atual",
  future: "futuro",
};

const columnLabel: Record<FlowColumn, string> = {
  planned: "previstas",
  realized: "realizadas",
  projected: "projetadas",
};

type RowDef = {
  label: string;
  value: (month: CashFlowMonth) => string | null;
  click?: { column: FlowColumn; direction: FlowDirection };
  strong?: boolean;
};

const ROWS: RowDef[] = [
  { label: "Saldo inicial", value: (m) => m.opening_balance },
  { label: "Entradas previstas", value: (m) => m.planned_in, click: { column: "planned", direction: "in" } },
  { label: "Entradas realizadas", value: (m) => m.realized_in, click: { column: "realized", direction: "in" } },
  { label: "Saídas previstas", value: (m) => m.planned_out, click: { column: "planned", direction: "out" } },
  { label: "Saídas realizadas", value: (m) => m.realized_out, click: { column: "realized", direction: "out" } },
  { label: "Entradas projetadas", value: (m) => m.projected_in, click: { column: "projected", direction: "in" } },
  { label: "Saídas projetadas", value: (m) => m.projected_out, click: { column: "projected", direction: "out" } },
  { label: "Saldo final realizado", value: (m) => m.closing_realized, strong: true },
  { label: "Saldo final projetado", value: (m) => m.closing_projected, strong: true },
];

export default function CashFlowPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [startMonth, setStartMonth] = useState(currentMonthIso(-1));
  const [months, setMonths] = useState(6);
  const [flow, setFlow] = useState<CashFlow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [loaded, setLoaded] = useState<{ key: string; items: FlowItem[] } | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user || !startMonth) return;
    let cancelled = false;
    getCashFlow(startMonth, months)
      .then((data) => {
        if (cancelled) return;
        setFlow(data);
        setError(null);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar o fluxo de caixa");
      });
    return () => {
      cancelled = true;
    };
  }, [user, startMonth, months]);

  const selectionKey = selection ? `${selection.month}|${selection.column}|${selection.direction}` : null;
  useEffect(() => {
    if (!selection || !selectionKey) return;
    let cancelled = false;
    getCashFlowItems(selection.month, selection.column, selection.direction)
      .then((items) => {
        if (!cancelled) setLoaded({ key: selectionKey, items });
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar os itens");
      });
    return () => {
      cancelled = true;
    };
  }, [selection, selectionKey]);

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const items = loaded && loaded.key === selectionKey ? loaded.items : null;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Fluxo de caixa</h1>
        <p className="text-muted-foreground text-sm">
          Por caixa: conta quando o dinheiro se move. Compra no cartão só sai do caixa quando a fatura é paga.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor="cf-start">Mês inicial</Label>
          <Input id="cf-start" type="month" value={startMonth} onChange={(event) => setStartMonth(event.target.value)} />
        </div>
        <div className="flex flex-col gap-2">
          <Label>Meses</Label>
          <div className="flex gap-1">
            {[3, 6, 12].map((value) => (
              <Button
                key={value}
                size="sm"
                variant={months === value ? "default" : "outline"}
                aria-pressed={months === value}
                onClick={() => setMonths(value)}
              >
                {value}
              </Button>
            ))}
          </div>
        </div>
        <Button
          variant="outline"
          onClick={() =>
            downloadCsv(cashFlowCsvPath(startMonth, months), `fluxo-de-caixa-${startMonth}.csv`).catch((caught) =>
              setError(caught instanceof Error ? caught.message : "erro ao exportar"),
            )
          }
        >
          Exportar CSV
        </Button>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {flow && (
        <>
          <Card>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div>
                <p className="text-muted-foreground text-sm">Dinheiro em caixa hoje (contas que não são cartão)</p>
                <p className="text-2xl font-semibold">{formatCurrency(flow.cash_balance_today)}</p>
              </div>
              <p className="text-muted-foreground max-w-md text-xs">
                Confira o saldo inicial de cada conta em{" "}
                <Link href="/accounts" className="underline">
                  Contas
                </Link>
                : sem ele o saldo não bate com o do banco.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-4">
              <CashFlowChart months={flow.months} />
            </CardContent>
          </Card>

          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="p-2 text-left"> </th>
                  {flow.months.map((month) => (
                    <th key={month.month} className="p-2 text-right whitespace-nowrap">
                      {monthLabel(month.month)}
                      <span className="text-muted-foreground block text-xs font-normal">{statusLabel[month.status]}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((row) => (
                  <tr key={row.label} className={row.strong ? "bg-muted/30 font-semibold" : ""}>
                    <td className="p-2 text-left whitespace-nowrap">{row.label}</td>
                    {flow.months.map((month) => {
                      const value = row.value(month);
                      const clickable = row.click && value !== null && Number(value) !== 0;
                      return (
                        <td key={month.month} className="p-2 text-right whitespace-nowrap">
                          {value === null ? (
                            <span className="text-muted-foreground">—</span>
                          ) : clickable && row.click ? (
                            <button
                              type="button"
                              className="underline decoration-dotted underline-offset-4"
                              aria-label={`Ver itens: ${row.label} de ${monthLabel(month.month)}`}
                              onClick={() =>
                                setSelection({ month: month.month, column: row.click!.column, direction: row.click!.direction })
                              }
                            >
                              {formatCurrency(value)}
                            </button>
                          ) : (
                            <span className={Number(value) < 0 && row.strong ? "text-destructive" : ""}>
                              {formatCurrency(value)}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selection && (
            <Card>
              <CardContent className="flex flex-col gap-2 py-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium">
                    {selection.direction === "in" ? "Entradas" : "Saídas"} {columnLabel[selection.column]} de{" "}
                    {monthLabel(selection.month)}
                  </p>
                  <Button size="sm" variant="ghost" onClick={() => setSelection(null)}>
                    Fechar
                  </Button>
                </div>
                {items === null && <p className="text-muted-foreground text-sm">Carregando...</p>}
                {items?.length === 0 && <p className="text-muted-foreground text-sm">Nenhum item.</p>}
                {items?.map((item, index) => (
                  <div key={`${item.when}-${index}`} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span>
                      {formatDate(item.when)} · {item.description}
                      <span className="text-muted-foreground">
                        {" "}
                        · {sourceLabels[item.source] ?? item.source}
                        {item.category_name && ` · ${item.category_name}`}
                      </span>
                    </span>
                    <span className="whitespace-nowrap">{formatCurrency(item.amount)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {flow.warnings.map((warning) => (
            <p key={warning} className="text-muted-foreground text-xs">
              {warning}
            </p>
          ))}
        </>
      )}
    </main>
  );
}
