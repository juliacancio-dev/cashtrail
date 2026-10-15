"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import { createInvestment, getBenchmark, getPortfolio, refreshQuotes } from "@/features/investments/api";
import { InvestmentForm } from "@/features/investments/investment-form";
import { InvestmentPanel } from "@/features/investments/investment-panel";
import type { AssetFormValues, Benchmark, Portfolio, Refresh } from "@/features/investments/schemas";
import { formatCurrency, formatDate } from "@/lib/format";

function pct(value: string | null): string {
  return value === null ? "—" : `${Number(value).toFixed(2).replace(".", ",")}%`;
}

export default function InvestmentsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [refresh, setRefresh] = useState<Refresh | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    Promise.all([listAccounts(), listCategories(), getPortfolio()])
      .then(([accountsData, categoriesData, portfolioData]) => {
        if (cancelled) return;
        setAccounts(accountsData);
        setCategories(categoriesData);
        setPortfolio(portfolioData);
      })
      .catch(() => {
        if (!cancelled) setError("nao foi possivel carregar a carteira");
      });
    // O comparativo depende de uma fonte externa: se falhar, a carteira segue sem ele.
    getBenchmark()
      .then((data) => {
        if (!cancelled) setBenchmark(data);
      })
      .catch(() => {
        if (!cancelled) setBenchmark(null);
      });
    return () => {
      cancelled = true;
    };
  }, [user, reloadKey]);

  async function handleCreate(values: AssetFormValues) {
    await createInvestment(values);
    setShowForm(false);
    setReloadKey((key) => key + 1);
  }

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      setRefresh(await refreshQuotes());
      setReloadKey((key) => key + 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao atualizar as cotações");
    } finally {
      setRefreshing(false);
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const investmentAccounts = accounts
    .filter((account) => account.type === "investment" && !account.is_archived)
    .map((account) => ({ id: account.id, name: account.name }));
  const cashAccounts = accounts
    .filter((account) => (account.type === "checking" || account.type === "savings") && !account.is_archived)
    .map((account) => ({ id: account.id, name: account.name }));
  const categoryOptions = categories
    .filter((category) => !category.is_archived)
    .map((category) => ({ id: category.id, name: category.name }));
  const totals = portfolio?.totals;

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Investimentos</h1>
          <p className="text-muted-foreground text-sm">
            Comprar não é despesa e a valorização não é receita: só ganhos realizados e proventos entram no
            resultado. O patrimônio usa o valor de mercado.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" disabled={refreshing} onClick={handleRefresh}>
            {refreshing ? "Atualizando..." : "Atualizar cotações"}
          </Button>
          {!showForm && <Button onClick={() => setShowForm(true)}>Novo ativo</Button>}
        </div>
      </div>

      {refresh && (
        <p className="text-muted-foreground text-sm">
          {refresh.updated.length} atualizada(s)
          {refresh.failed.length > 0 && ` · sem resposta: ${refresh.failed.join(", ")} (mantida a última cotação)`}
          {refresh.skipped_for_cap.length > 0 &&
            ` · não consultadas por limite mensal: ${refresh.skipped_for_cap.join(", ")}`}
          {` · ${refresh.requests_this_month}/${refresh.monthly_cap} requisições no mês`}
        </p>
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {totals && (
        <Card>
          <CardContent className="grid gap-3 py-4 sm:grid-cols-4">
            <div>
              <p className="text-muted-foreground text-xs">Valor de mercado</p>
              <p className="text-xl font-semibold">{formatCurrency(totals.market_value)}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Custo</p>
              <p className="text-xl font-semibold">{formatCurrency(totals.cost)}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Resultado não realizado</p>
              <p className={`text-xl font-semibold ${Number(totals.unrealized) < 0 ? "text-destructive" : ""}`}>
                {formatCurrency(totals.unrealized)}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Retorno total</p>
              <p className="text-xl font-semibold">
                {formatCurrency(totals.total_return)} ({pct(totals.total_return_pct)})
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {benchmark && benchmark.since && (
        <div className="rounded-lg border p-4 text-sm">
          <p>
            Desde {formatDate(benchmark.since)}: carteira <strong>{pct(benchmark.portfolio_return_pct)}</strong> ·
            CDI <strong>{pct(benchmark.cdi_return_pct)}</strong>
            {benchmark.difference_pct !== null && ` · diferença ${pct(benchmark.difference_pct)}`}
          </p>
          <p className="text-muted-foreground mt-1 text-xs">{benchmark.note}</p>
        </div>
      )}

      {portfolio?.warnings.map((warning) => (
        <p key={warning} className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm">
          {warning}
        </p>
      ))}

      {showForm && (
        <InvestmentForm
          key={investmentAccounts.map((account) => account.id).join(",")}
          accounts={investmentAccounts}
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      {portfolio === null ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : portfolio.positions.length === 0 ? (
        <p className="text-muted-foreground text-sm">Nenhum ativo cadastrado ainda.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {portfolio.positions.map((position) => (
            <InvestmentPanel
              key={position.id}
              position={position}
              cashAccounts={cashAccounts}
              categories={categoryOptions}
              onChanged={() => setReloadKey((key) => key + 1)}
            />
          ))}
        </div>
      )}
    </main>
  );
}
