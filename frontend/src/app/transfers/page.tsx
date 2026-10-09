"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { createTransfer, deleteTransfer, listTransfers } from "@/features/transfers/api";
import type { Transfer, TransferFormValues } from "@/features/transfers/schemas";
import { TransferForm } from "@/features/transfers/transfer-form";
import { TransferList } from "@/features/transfers/transfer-list";

export default function TransfersPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    Promise.all([listAccounts(), listTransfers()])
      .then(([accountsData, transfersData]) => {
        setAccounts(accountsData);
        setTransfers(transfersData);
      })
      .catch(() => setError("nao foi possivel carregar as transferencias"));
  }, [user]);

  async function handleCreate(values: TransferFormValues) {
    const created = await createTransfer(values);
    setTransfers((current) => [...current, created]);
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      await deleteTransfer(id);
      setTransfers((current) => current.filter((t) => t.id !== id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao desfazer a transferencia");
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const active = accounts.filter((a) => !a.is_archived);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Transferências</h1>
        <p className="text-muted-foreground text-sm">
          Mover dinheiro entre as suas contas não é receita nem despesa: não entra no dashboard nem nos orçamentos.
        </p>
      </div>

      {active.length < 2 ? (
        <p className="text-muted-foreground text-sm">Cadastre ao menos duas contas para transferir entre elas.</p>
      ) : (
        <TransferForm accounts={active} onCreate={handleCreate} />
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      <TransferList transfers={transfers} accounts={accounts} onDelete={handleDelete} />
    </main>
  );
}
