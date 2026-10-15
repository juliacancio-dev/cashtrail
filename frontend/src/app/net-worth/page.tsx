"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { kindLabel } from "@/features/assets/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { NetWorthChart } from "@/features/reports/net-worth-chart";
import { downloadCsv, getNetWorth, getNetWorthHistory, netWorthCsvPath } from "@/features/reports/api";
import type { NetWorth, NetWorthPoint } from "@/features/reports/schemas";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";

function Row({ label, value, hint, strong }: { label: string; value: string; hint?: string; strong?: boolean }) {
  return (
    <div className={`flex items-baseline justify-between gap-3 py-1 ${strong ? "border-t pt-2 font-semibold" : ""}`}>
      <span>
        {label}
        {hint && <span className="text-muted-foreground block text-xs font-normal">{hint}</span>}
      </span>
      <span className="whitespace-nowrap">{formatCurrency(value)}</span>
    </div>
  );
}

export default function NetWorthPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [asOf, setAsOf] = useState(todayIso());
  const [worth, setWorth] = useState<NetWorth | null>(null);
  const [history, setHistory] = useState<NetWorthPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user || !asOf) return;
    let cancelled = false;
    getNetWorth(asOf)
      .then((data) => {
        if (cancelled) return;
        setWorth(data);
        setError(null);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar o balanço");
      });
    return () => {
      cancelled = true;
    };
  }, [user, asOf]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    getNetWorthHistory(12)
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch(() => {
        if (!cancelled) setHistory([]);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const isToday = asOf === todayIso();

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Patrimônio</h1>
        <p className="text-muted-foreground text-sm">
          Ativos menos passivos. Transferir, pagar fatura ou amortizar dívida não muda o patrimônio; só o resultado
          (receitas e despesas) e o valor dos bens mudam.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor="nw-as-of">Posição em</Label>
          <Input id="nw-as-of" type="date" max={todayIso()} value={asOf} onChange={(event) => setAsOf(event.target.value)} />
        </div>
        <Button
          variant="outline"
          onClick={() =>
            downloadCsv(netWorthCsvPath(asOf), `patrimonio-${asOf}.csv`).catch((caught) =>
              setError(caught instanceof Error ? caught.message : "erro ao exportar"),
            )
          }
        >
          Exportar CSV
        </Button>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {worth && (
        <>
          <Card>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div>
                <p className="text-muted-foreground text-sm">Patrimônio líquido em {formatDate(worth.as_of)}</p>
                <p className={`text-3xl font-semibold ${Number(worth.net_worth) < 0 ? "text-destructive" : ""}`}>
                  {formatCurrency(worth.net_worth)}
                </p>
              </div>
              <p className="text-muted-foreground text-sm">
                Ativos {formatCurrency(worth.total_assets)} − passivos {formatCurrency(worth.total_liabilities)}
              </p>
            </CardContent>
          </Card>

          {worth.warnings.map((warning) => (
            <p key={warning} className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm">
              {warning}{" "}
              {warning.includes("bens") && (
                <Link href="/assets" className="underline">
                  Ver bens
                </Link>
              )}
            </p>
          ))}

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardContent className="flex flex-col py-4">
                <h2 className="mb-2 font-medium">Ativos</h2>
                <p className="text-muted-foreground text-xs font-medium">Caixa e contas</p>
                {worth.cash.length === 0 && <p className="text-muted-foreground text-sm">Nenhuma conta.</p>}
                {worth.cash.map((item) => (
                  <Row key={item.account_id} label={item.name} value={item.amount} />
                ))}
                <p className="text-muted-foreground mt-2 text-xs font-medium">Bens</p>
                {worth.assets.length === 0 && (
                  <p className="text-muted-foreground text-sm">
                    Nenhum bem.{" "}
                    <Link href="/assets" className="underline">
                      Cadastrar
                    </Link>
                  </p>
                )}
                {worth.assets.map((item) => (
                  <Row
                    key={item.asset_id}
                    label={item.name}
                    value={item.value}
                    hint={[
                      kindLabel(item.kind),
                      item.valued_at ? `avaliado em ${formatDate(item.valued_at)}` : null,
                      item.debt_outstanding !== null
                        ? `seu: ${formatCurrency(item.equity)} (financiado ${formatCurrency(item.debt_outstanding)})`
                        : null,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  />
                ))}
                <p className="text-muted-foreground mt-2 text-xs font-medium">Investimentos (valor de mercado)</p>
                {worth.investments.length === 0 && (
                  <p className="text-muted-foreground text-sm">
                    Nenhum investimento.{" "}
                    <Link href="/investments" className="underline">
                      Cadastrar
                    </Link>
                  </p>
                )}
                {worth.investments.map((item) => (
                  <Row
                    key={item.asset_id}
                    label={item.name}
                    value={item.market_value}
                    hint={
                      item.has_quote
                        ? `custo ${formatCurrency(item.cost)} · resultado ${formatCurrency(item.unrealized)}`
                        : "sem cotação: valor pelo custo"
                    }
                  />
                ))}
                <Row label="Total dos ativos" value={worth.total_assets} strong />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex flex-col py-4">
                <h2 className="mb-2 font-medium">Passivos</h2>
                <p className="text-muted-foreground text-xs font-medium">Cartões de crédito</p>
                {worth.cards.length === 0 && <p className="text-muted-foreground text-sm">Nenhum cartão.</p>}
                {worth.cards.map((item) => (
                  <Row key={item.account_id} label={item.name} value={item.amount} />
                ))}
                <p className="text-muted-foreground mt-2 text-xs font-medium">Dívidas e financiamentos</p>
                {worth.debts.length === 0 && <p className="text-muted-foreground text-sm">Nenhuma dívida.</p>}
                {worth.debts.map((item) => (
                  <Row
                    key={item.account_id}
                    label={item.name}
                    value={item.amount}
                    hint={
                      item.short_term !== null && item.long_term !== null
                        ? `curto prazo ${formatCurrency(item.short_term)} · longo prazo ${formatCurrency(item.long_term)}`
                        : undefined
                    }
                  />
                ))}
                {worth.debts_short_term !== null && worth.debts_long_term !== null && worth.debts.length > 0 && (
                  <p className="text-muted-foreground text-xs">
                    Dívidas: curto prazo (até 12 meses) {formatCurrency(worth.debts_short_term)} · longo prazo{" "}
                    {formatCurrency(worth.debts_long_term)}
                  </p>
                )}
                <Row label="Total dos passivos" value={worth.total_liabilities} strong />
              </CardContent>
            </Card>
          </div>

          {!isToday && (
            <p className="text-muted-foreground text-xs">
              Em datas passadas o curto e o longo prazo não são mostrados (dependem das parcelas em aberto de hoje).
            </p>
          )}
        </>
      )}

      <Card>
        <CardContent className="py-4">
          <h2 className="mb-1 font-medium">Evolução (12 meses)</h2>
          <p className="text-muted-foreground mb-3 text-xs">
            Calculada do histórico de lançamentos e avaliações. Antes do primeiro uso do app só existe o saldo
            inicial das contas.
          </p>
          {history.length > 0 ? <NetWorthChart points={history} /> : <p className="text-sm">Sem dados.</p>}
        </CardContent>
      </Card>
    </main>
  );
}
