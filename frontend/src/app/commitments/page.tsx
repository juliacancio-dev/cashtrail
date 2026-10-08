"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import { createCommitments, getCommitmentSummary, listCommitments } from "@/features/commitments/api";
import { CommitmentForm } from "@/features/commitments/commitment-form";
import { CommitmentList } from "@/features/commitments/commitment-list";
import {
  statusFilterOptions,
  type CommitmentFormValues,
  type CommitmentList as CommitmentListData,
  type CommitmentSummary,
  type Direction,
  type StatusFilter,
} from "@/features/commitments/schemas";
import { CommitmentSummaryCards } from "@/features/commitments/summary-cards";
import { formatCurrency } from "@/lib/format";

const ALL = "all";

export default function CommitmentsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [data, setData] = useState<CommitmentListData | null>(null);
  const [summary, setSummary] = useState<CommitmentSummary | null>(null);
  const [direction, setDirection] = useState<Direction | typeof ALL>(ALL);
  const [status, setStatus] = useState<StatusFilter | typeof ALL>("pending");
  const [categoryId, setCategoryId] = useState<string>(ALL);
  const [dueFrom, setDueFrom] = useState("");
  const [dueTo, setDueTo] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

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
      .catch(() => setError("nao foi possivel carregar contas e categorias"));
  }, [user]);

  // Recarrega a lista e o resumo quando o filtro muda ou depois de qualquer ação (reloadKey).
  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    Promise.all([
      listCommitments({
        direction: direction === ALL ? undefined : direction,
        status: status === ALL ? undefined : status,
        category_id: categoryId === ALL ? undefined : categoryId,
        due_from: dueFrom || undefined,
        due_to: dueTo || undefined,
      }),
      getCommitmentSummary(),
    ])
      .then(([list, sum]) => {
        if (cancelled) return;
        setData(list);
        setSummary(sum);
        setError(null);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar as contas");
      });
    return () => {
      cancelled = true;
    };
  }, [user, direction, status, categoryId, dueFrom, dueTo, reloadKey]);

  const refresh = useCallback(async () => {
    setReloadKey((key) => key + 1);
  }, []);

  async function handleCreate(values: CommitmentFormValues) {
    setFormError(null);
    try {
      await createCommitments(values);
      setShowForm(false);
      await refresh();
    } catch (caught) {
      setFormError(caught instanceof Error ? caught.message : "erro ao criar a conta");
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
  const ready = activeAccounts.length > 0 && activeCategories.length > 0;
  const categoryItems = [{ value: ALL, label: "Todas as categorias" }, ...categories.map((c) => ({ value: c.id, label: c.name }))];

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
          <h1 className="text-2xl font-semibold">Contas a pagar e a receber</h1>
          <p className="text-muted-foreground text-sm">{user.email}</p>
        </div>
        <Button onClick={() => setShowForm((value) => !value)} disabled={!ready}>
          {showForm ? "Fechar formulário" : "Nova conta"}
        </Button>
      </div>

      {!ready && (
        <p className="text-muted-foreground text-sm">
          Cadastre ao menos uma conta bancária e uma categoria antes de criar compromissos.
        </p>
      )}

      {summary && <CommitmentSummaryCards summary={summary} />}

      {showForm && ready && (
        <>
          {formError && <p className="text-destructive text-sm">{formError}</p>}
          <CommitmentForm
            accounts={activeAccounts}
            categories={activeCategories}
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
          />
        </>
      )}

      <div className="flex flex-wrap items-end gap-3" role="group" aria-label="Filtros">
        <div className="flex gap-1">
          {([[ALL, "Todas"], ["payable", "A pagar"], ["receivable", "A receber"]] as const).map(([value, label]) => (
            <Button
              key={value}
              size="sm"
              variant={direction === value ? "default" : "outline"}
              aria-pressed={direction === value}
              onClick={() => setDirection(value)}
            >
              {label}
            </Button>
          ))}
        </div>

        <div className="flex flex-col gap-1">
          <Label>Situação</Label>
          <Select value={status} onValueChange={(value) => setStatus(value as StatusFilter | typeof ALL)} items={statusFilterOptions}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {statusFilterOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <Label>Categoria</Label>
          <Select value={categoryId} onValueChange={(value) => setCategoryId(value as string)} items={categoryItems}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {categoryItems.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <Label htmlFor="due-from">Vence de</Label>
          <Input id="due-from" type="date" value={dueFrom} onChange={(event) => setDueFrom(event.target.value)} />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="due-to">até</Label>
          <Input id="due-to" type="date" value={dueTo} onChange={(event) => setDueTo(event.target.value)} />
        </div>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {data && (
        <>
          <p className="text-muted-foreground text-sm">
            {data.totals.count} conta(s) · saldo a pagar {formatCurrency(data.totals.payable_balance)} · saldo a
            receber {formatCurrency(data.totals.receivable_balance)}
          </p>
          <CommitmentList items={data.items} accounts={accounts} categories={categories} onChanged={refresh} />
        </>
      )}
    </main>
  );
}
