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
import { GoalForm } from "@/features/goals/goal-form";
import { GoalList } from "@/features/goals/goal-list";
import { contributeToGoal, createGoal, deleteGoal, listGoals } from "@/features/goals/api";
import type { ContributionFormValues, CreateGoalFormValues, Goal } from "@/features/goals/schemas";

export default function GoalsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [goals, setGoals] = useState<Goal[]>([]);
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
    Promise.all([listGoals(), listAccounts(), listCategories()])
      .then(([goalsData, accountsData, categoriesData]) => {
        setGoals(goalsData);
        setAccounts(accountsData);
        setCategories(categoriesData);
      })
      .catch(() => setError("nao foi possivel carregar as metas"))
      .finally(() => setIsLoadingData(false));
  }, [user]);

  async function handleCreate(values: CreateGoalFormValues) {
    setError(null);
    try {
      const goal = await createGoal(values);
      setGoals((current) => [...current, goal]);
    } catch {
      setError("nao foi possivel criar a meta");
    }
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      await deleteGoal(id);
      setGoals((current) => current.filter((g) => g.id !== id));
    } catch {
      setError("nao foi possivel excluir a meta");
    }
  }

  async function handleContribute(goalId: string, values: ContributionFormValues) {
    setError(null);
    try {
      await contributeToGoal(goalId, values);
      const refreshed = await listGoals();
      setGoals(refreshed);
    } catch {
      setError("nao foi possivel registrar a contribuicao");
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
        <h1 className="text-2xl font-semibold">Metas</h1>
        <p className="text-muted-foreground text-sm">{user.email}</p>
      </div>

      <GoalForm onCreate={handleCreate} />

      {error && <p className="text-destructive text-sm">{error}</p>}

      {!isLoadingData && (
        <GoalList
          goals={goals}
          accounts={activeAccounts}
          categories={activeCategories}
          onDelete={handleDelete}
          onContribute={handleContribute}
        />
      )}
    </main>
  );
}
