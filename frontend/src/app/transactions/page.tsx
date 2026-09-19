"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { AppNav } from "@/components/app-nav";
import { useAuth } from "@/features/auth/auth-context";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import { TransactionForm } from "@/features/transactions/transaction-form";
import { TransactionList } from "@/features/transactions/transaction-list";
import { createTransaction, listTransactions } from "@/features/transactions/api";
import type { CreateTransactionFormValues, Transaction } from "@/features/transactions/schemas";

export default function TransactionsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    Promise.all([listTransactions(), listAccounts(), listCategories()])
      .then(([transactionsData, accountsData, categoriesData]) => {
        setTransactions(transactionsData);
        setAccounts(accountsData);
        setCategories(categoriesData);
      })
      .catch(() => setError("nao foi possivel carregar os lancamentos"))
      .finally(() => setIsLoadingData(false));
  }, [user]);

  async function handleCreate(values: CreateTransactionFormValues) {
    setError(null);
    try {
      const transaction = await createTransaction(values);
      setTransactions((current) => [...current, transaction]);
    } catch {
      setError("nao foi possivel criar o lancamento");
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

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Lançamentos</h1>
        <p className="text-muted-foreground text-sm">{user.email}</p>
      </div>

      {isLoadingData ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : activeAccounts.length === 0 || activeCategories.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Cadastre ao menos uma conta e uma categoria antes de lançar.
        </p>
      ) : (
        <TransactionForm accounts={activeAccounts} categories={activeCategories} onCreate={handleCreate} />
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {!isLoadingData && (
        <TransactionList transactions={transactions} accounts={accounts} categories={categories} />
      )}
    </main>
  );
}
