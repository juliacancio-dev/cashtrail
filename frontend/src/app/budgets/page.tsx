"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { AppNav } from "@/components/app-nav";
import { useAuth } from "@/features/auth/auth-context";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import { BudgetForm } from "@/features/budgets/budget-form";
import { BudgetList } from "@/features/budgets/budget-list";
import { createBudget, deleteBudget, listBudgets } from "@/features/budgets/api";
import type { Budget, CreateBudgetFormValues } from "@/features/budgets/schemas";

export default function BudgetsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [budgets, setBudgets] = useState<Budget[]>([]);
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
    Promise.all([listBudgets(), listCategories()])
      .then(([budgetsData, categoriesData]) => {
        setBudgets(budgetsData);
        setCategories(categoriesData);
      })
      .catch(() => setError("nao foi possivel carregar os orcamentos"))
      .finally(() => setIsLoadingData(false));
  }, [user]);

  async function handleCreate(values: CreateBudgetFormValues) {
    const budget = await createBudget(values);
    setBudgets((current) => [...current, budget]);
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      await deleteBudget(id);
      setBudgets((current) => current.filter((b) => b.id !== id));
    } catch {
      setError("nao foi possivel excluir o orcamento");
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

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
        <h1 className="text-2xl font-semibold">Orçamentos</h1>
        <p className="text-muted-foreground text-sm">{user.email}</p>
      </div>

      {isLoadingData ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : activeCategories.length === 0 ? (
        <p className="text-muted-foreground text-sm">Cadastre ao menos uma categoria antes de orçar.</p>
      ) : (
        <BudgetForm categories={activeCategories} onCreate={handleCreate} />
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {!isLoadingData && <BudgetList budgets={budgets} onDelete={handleDelete} />}
    </main>
  );
}
