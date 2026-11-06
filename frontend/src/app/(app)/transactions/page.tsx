"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-context";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import { TransactionForm } from "@/features/transactions/transaction-form";
import { TransactionList } from "@/features/transactions/transaction-list";
import { createTransaction, listTransactions } from "@/features/transactions/api";
import type { CreateTransactionFormValues, Transaction } from "@/features/transactions/schemas";
import { currentMonthIso, formatCurrency, monthName, shiftMonth } from "@/lib/format";

// Lançamentos (doc 33, decisão 3): um mês por vez, agrupado por dia, formulário atrás do botão.
export default function TransactionsPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [month, setMonth] = useState(() => currentMonthIso());
  const [transactions, setTransactions] = useState<Transaction[] | null>(null);
  const [loadedMonth, setLoadedMonth] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [optionsLoaded, setOptionsLoaded] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    Promise.all([listAccounts(), listCategories()])
      .then(([accountsData, categoriesData]) => {
        setAccounts(accountsData);
        setCategories(categoriesData);
      })
      .catch(() => setError("Não foi possível carregar contas e categorias."))
      .finally(() => setOptionsLoaded(true));
  }, [user]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    listTransactions(month)
      .then((data) => {
        if (!active) return;
        setTransactions(data);
        setLoadedMonth(month);
        setError(null);
      })
      .catch(() => active && setError("Não foi possível carregar os lançamentos."));
    return () => {
      active = false;
    };
  }, [user, month, reloadKey]);

  async function handleCreate(values: CreateTransactionFormValues) {
    setError(null);
    try {
      await createTransaction(values);
      // Mostra o mês do lançamento novo, para ele aparecer na lista.
      setMonth(values.occurred_at.slice(0, 7));
      setReloadKey((key) => key + 1);
    } catch {
      setError("Não foi possível criar o lançamento.");
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const activeAccounts = accounts.filter((a) => !a.is_archived);
  const activeCategories = categories.filter((c) => !c.is_archived);
  const canCreate = activeAccounts.length > 0 && activeCategories.length > 0;
  const isCurrent = month === currentMonthIso();
  const year = Number(month.slice(0, 4));
  const title = `Lançamentos de ${monthName(month)}${year !== new Date().getFullYear() ? ` de ${year}` : ""}`;
  const ready = transactions && loadedMonth === month;
  const income = ready ? transactions.filter((t) => t.type === "income").reduce((s, t) => s + Number(t.amount), 0) : 0;
  const expense = ready ? transactions.filter((t) => t.type === "expense").reduce((s, t) => s + Number(t.amount), 0) : 0;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <h1 className="text-2xl font-semibold">{title}</h1>
          <div className="flex gap-1">
            <Button variant="ghost" className="size-11 rounded-full" aria-label="Mês anterior" onClick={() => setMonth((m) => shiftMonth(m, -1))}>
              ‹
            </Button>
            {!isCurrent && (
              <Button variant="ghost" className="min-h-11 rounded-full" onClick={() => setMonth(currentMonthIso())}>
                Este mês
              </Button>
            )}
            <Button variant="ghost" className="size-11 rounded-full" aria-label="Próximo mês" onClick={() => setMonth((m) => shiftMonth(m, 1))}>
              ›
            </Button>
          </div>
        </div>
        <Button
          className="min-h-11"
          aria-expanded={showForm}
          aria-controls="novo-lancamento"
          disabled={!canCreate}
          onClick={() => setShowForm((open) => !open)}
        >
          {showForm ? "Fechar formulário" : "Novo lançamento"}
        </Button>
      </div>

      {optionsLoaded && !canCreate && (
        <p className="text-muted-foreground text-sm">Cadastre ao menos uma conta e uma categoria antes de lançar.</p>
      )}

      {showForm && canCreate && (
        <section id="novo-lancamento" aria-label="Novo lançamento" className="border-border bg-card rounded-xl border p-4">
          <TransactionForm accounts={activeAccounts} categories={activeCategories} onCreate={handleCreate} />
        </section>
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {!ready ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : (
        <>
          {transactions.length > 0 && (
            <p className="text-muted-foreground">
              {transactions.length} {transactions.length === 1 ? "lançamento" : "lançamentos"} · entraram{" "}
              <span className="text-income font-mono">{formatCurrency(income)}</span> e saíram{" "}
              <span className="text-expense font-mono">{formatCurrency(expense)}</span>
            </p>
          )}
          <TransactionList transactions={transactions} accounts={accounts} categories={categories} />
        </>
      )}
    </main>
  );
}
