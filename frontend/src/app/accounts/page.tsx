"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-context";
import { AccountForm } from "@/features/accounts/account-form";
import { AccountList } from "@/features/accounts/account-list";
import { archiveAccount, createAccount, listAccounts } from "@/features/accounts/api";
import type { Account, CreateAccountFormValues } from "@/features/accounts/schemas";

export default function AccountsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    listAccounts()
      .then(setAccounts)
      .catch(() => setError("nao foi possivel carregar as contas"))
      .finally(() => setIsLoadingAccounts(false));
  }, [user]);

  async function handleCreate(values: CreateAccountFormValues) {
    setError(null);
    try {
      const account = await createAccount(values.name, values.type);
      setAccounts((current) => [...current, account]);
    } catch {
      setError("nao foi possivel criar a conta");
    }
  }

  async function handleArchive(id: string) {
    setError(null);
    try {
      const updated = await archiveAccount(id);
      setAccounts((current) => current.map((a) => (a.id === id ? updated : a)));
    } catch {
      setError("nao foi possivel arquivar a conta");
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Minhas contas</h1>
          <p className="text-muted-foreground text-sm">{user.email}</p>
        </div>
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <AccountForm onCreate={handleCreate} />

      {error && <p className="text-destructive text-sm">{error}</p>}

      {isLoadingAccounts ? (
        <p className="text-muted-foreground text-sm">Carregando contas...</p>
      ) : (
        <AccountList accounts={accounts} onArchive={handleArchive} />
      )}
    </main>
  );
}
