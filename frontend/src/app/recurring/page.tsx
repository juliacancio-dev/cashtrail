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
import { RecurringForm } from "@/features/recurring/recurring-form";
import { RecurringList } from "@/features/recurring/recurring-list";
import { createRecurring, deactivateRecurring, listRecurring } from "@/features/recurring/api";
import type { CreateRecurringFormValues, Recurring } from "@/features/recurring/schemas";

export default function RecurringPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Recurring[]>([]);
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
    Promise.all([listRecurring(), listAccounts(), listCategories()])
      .then(([recurringData, accountsData, categoriesData]) => {
        setItems(recurringData);
        setAccounts(accountsData);
        setCategories(categoriesData);
      })
      .catch(() => setError("nao foi possivel carregar as recorrencias"))
      .finally(() => setIsLoadingData(false));
  }, [user]);

  async function handleCreate(values: CreateRecurringFormValues) {
    const recurring = await createRecurring(values);
    setItems((current) => [...current, recurring]);
  }

  async function handleDeactivate(id: string) {
    setError(null);
    try {
      const updated = await deactivateRecurring(id);
      setItems((current) => current.map((r) => (r.id === id ? updated : r)));
    } catch {
      setError("nao foi possivel cancelar a recorrencia");
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
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Recorrências</h1>
        <p className="text-muted-foreground text-sm">{user.email}</p>
      </div>

      {isLoadingData ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : activeAccounts.length === 0 || activeCategories.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Cadastre ao menos uma conta e uma categoria antes de criar uma recorrência.
        </p>
      ) : (
        <RecurringForm accounts={activeAccounts} categories={activeCategories} onCreate={handleCreate} />
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {!isLoadingData && (
        <RecurringList
          items={items}
          accounts={accounts}
          categories={categories}
          onDeactivate={handleDeactivate}
        />
      )}
    </main>
  );
}
