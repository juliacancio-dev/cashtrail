"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-context";
import { downloadCsv, dreCsvPath, getDre } from "@/features/reports/api";
import type { Dre, DreLine } from "@/features/reports/schemas";
import {
  firstDayOfCurrentMonthIso,
  formatCurrency,
  formatDate,
  lastDayOfCurrentMonthIso,
} from "@/lib/format";

function signed(value: string): string {
  const number = Number(value);
  return `${number > 0 ? "+ " : number < 0 ? "− " : ""}${formatCurrency(Math.abs(number))}`;
}

function LineRow({ line }: { line: DreLine }) {
  const isSubtotal = line.kind === "subtotal";
  const isFinal = line.key === "net_result";
  const variation = Number(line.amount) - Number(line.previous_amount);

  return (
    <>
      <tr className={isSubtotal ? "border-t bg-muted/40 font-semibold" : line.kind === "ungrouped" ? "text-muted-foreground" : ""}>
        <td className="p-2">{line.label}</td>
        <td className={`p-2 text-right whitespace-nowrap ${isFinal && Number(line.amount) < 0 ? "text-destructive" : ""}`}>
          {isFinal ? signed(line.amount) : formatCurrency(line.amount)}
        </td>
        <td className="p-2 text-right whitespace-nowrap text-muted-foreground">
          {line.percent_of_net_revenue !== null ? `${Number(line.percent_of_net_revenue).toFixed(1).replace(".", ",")}%` : "—"}
        </td>
        <td className="p-2 text-right whitespace-nowrap text-muted-foreground">{formatCurrency(line.previous_amount)}</td>
        <td className="p-2 text-right whitespace-nowrap text-muted-foreground">{variation === 0 ? "—" : signed(String(variation))}</td>
      </tr>
      {line.categories.map((category) => (
        <tr key={`${line.key}-${category.category_id}`} className="text-muted-foreground">
          <td className="py-1 pr-2 pl-8 text-sm">{category.name}</td>
          <td className="py-1 px-2 text-right text-sm whitespace-nowrap">{formatCurrency(category.amount)}</td>
          <td />
          <td />
          <td />
        </tr>
      ))}
    </>
  );
}

export default function DrePage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [startDate, setStartDate] = useState(firstDayOfCurrentMonthIso());
  const [endDate, setEndDate] = useState(lastDayOfCurrentMonthIso());
  const [includeForecast, setIncludeForecast] = useState(false);
  const [dre, setDre] = useState<Dre | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user || !startDate || !endDate || endDate < startDate) return;
    let cancelled = false;
    getDre(startDate, endDate, includeForecast)
      .then((data) => {
        if (cancelled) return;
        setDre(data);
        setError(null);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar o DRE");
      });
    return () => {
      cancelled = true;
    };
  }, [user, startDate, endDate, includeForecast]);

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const invalidPeriod = endDate < startDate;

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">DRE — resultado do período</h1>
        <p className="text-muted-foreground text-sm">
          Por competência: a compra no cartão conta na data da compra, e transferências não entram.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor="dre-start">De</Label>
          <Input id="dre-start" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="dre-end">Até</Label>
          <Input id="dre-end" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        </div>
        <label className="flex items-center gap-2 pb-2 text-sm">
          <input
            type="checkbox"
            checked={includeForecast}
            onChange={(event) => setIncludeForecast(event.target.checked)}
          />
          Incluir previsto (contas a pagar/receber em aberto)
        </label>
        <Button
          variant="outline"
          disabled={invalidPeriod}
          onClick={() =>
            downloadCsv(dreCsvPath(startDate, endDate, includeForecast), `dre-${startDate}-${endDate}.csv`).catch(
              (caught) => setError(caught instanceof Error ? caught.message : "erro ao exportar"),
            )
          }
        >
          Exportar CSV
        </Button>
      </div>

      {invalidPeriod && <p className="text-destructive text-sm">A data final não pode ser anterior à inicial.</p>}
      {error && <p className="text-destructive text-sm">{error}</p>}

      {dre && dre.ungrouped_count > 0 && (
        <p className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm">
          {dre.ungrouped_count} categoria(s) com movimento estão sem grupo e aparecem à parte. Classifique em{" "}
          <Link href="/categories" className="underline">
            Categorias
          </Link>{" "}
          para o DRE ficar completo.
        </p>
      )}

      {dre && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <caption className="text-muted-foreground p-2 text-left text-xs">
              {formatDate(dre.start_date)} a {formatDate(dre.end_date)} · comparado com{" "}
              {formatDate(dre.previous_start_date)} a {formatDate(dre.previous_end_date)}
              {dre.include_forecast && " · inclui previsto"}
            </caption>
            <thead className="bg-muted/50 text-left">
              <tr>
                <th className="p-2">Linha</th>
                <th className="p-2 text-right">Valor</th>
                <th className="p-2 text-right">% da receita líquida</th>
                <th className="p-2 text-right">Período anterior</th>
                <th className="p-2 text-right">Variação</th>
              </tr>
            </thead>
            <tbody>
              {dre.lines.map((line) => (
                <LineRow key={line.key} line={line} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
