"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import { createDebt, getDebtsSummary, listDebts } from "@/features/debts/api";
import { DebtForm } from "@/features/debts/debt-form";
import { DebtPanel } from "@/features/debts/debt-panel";
import type { Debt, DebtFormValues, DebtsSummary } from "@/features/debts/schemas";
import { formatCurrency, formatDate } from "@/lib/format";

export default function DebtsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [debts, setDebts] = useState<Debt[] | null>(null);
  const [summary, setSummary] = useState<DebtsSummary | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    Promise.all([listAccounts(), listCategories(), listDebts(), getDebtsSummary()])
      .then(([accountsData, categoriesData, debtsData, summaryData]) => {
        if (cancelled) return;
        setAccounts(accountsData);
        setCategories(categoriesData);
        setDebts(debtsData);
        setSummary(summaryData);
      })
      .catch(() => {
        if (!cancelled) setError("nao foi possivel carregar as dividas");
      });
    return () => {
      cancelled = true;
    };
  }, [user, reloadKey]);

  async function handleCreate(values: DebtFormValues) {
    await createDebt(values);
    setShowForm(false);
    setReloadKey((key) => key + 1);
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const payableAccounts = accounts
    .filter((account) => !account.is_archived && (account.type === "checking" || account.type === "savings"))
    .map((account) => ({ id: account.id, name: account.name }));
  const categoryOptions = categories
    .filter((category) => !category.is_archived)
    .map((category) => ({ id: category.id, name: category.name }));

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
          <h1 className="text-2xl font-semibold">Dívidas e financiamentos</h1>
          <p className="text-muted-foreground text-sm">
            Receber o empréstimo e devolver o principal não são receita nem despesa: só os juros e encargos entram
            no resultado.
          </p>
        </div>
        {!showForm && <Button onClick={() => setShowForm(true)}>Nova dívida</Button>}
      </div>

      {summary && summary.active_count > 0 && (
        <div className="rounded-lg border p-4 text-sm">
          <p>
            Saldo devedor total <strong>{formatCurrency(summary.outstanding_total)}</strong> em{" "}
            {summary.active_count} dívida(s)
            {summary.next_due_date &&
              ` · próxima parcela ${formatCurrency(summary.next_amount ?? 0)} em ${formatDate(summary.next_due_date)}`}
            {summary.overdue_count > 0 && ` · ${summary.overdue_count} com parcela atrasada`}
          </p>
        </div>
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {showForm && (
        <DebtForm
          accounts={payableAccounts}
          categories={categoryOptions}
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      {debts === null ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : debts.length === 0 ? (
        <p className="text-muted-foreground text-sm">Nenhuma dívida cadastrada ainda.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {debts.map((debt) => (
            <DebtPanel
              key={debt.id}
              debt={debt}
              accounts={payableAccounts}
              onChanged={() => setReloadKey((key) => key + 1)}
            />
          ))}
        </div>
      )}
    </main>
  );
}
