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
import { ImportWizard } from "@/features/statement-import/import-wizard";

export default function ImportPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
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
    Promise.all([listAccounts(), listCategories()])
      .then(([accountsData, categoriesData]) => {
        setAccounts(accountsData);
        setCategories(categoriesData);
      })
      .catch(() => setError("nao foi possivel carregar contas e categorias"))
      .finally(() => setIsLoadingData(false));
  }, [user]);

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
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Importar extrato</h1>
        <p className="text-muted-foreground text-sm">
          Envie o CSV do seu banco, revise as linhas e confirme. Nada é salvo antes da confirmação.
        </p>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {isLoadingData ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : activeAccounts.length === 0 || activeCategories.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Cadastre ao menos uma conta e uma categoria antes de importar.
        </p>
      ) : (
        <ImportWizard accounts={activeAccounts} categories={activeCategories} />
      )}
    </main>
  );
}
