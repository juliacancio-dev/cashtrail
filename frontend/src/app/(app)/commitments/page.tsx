"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

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
import { formatCurrency } from "@/lib/format";

const ALL = "all";

export default function CommitmentsPage() {
  const { user, isLoading } = useAuth();
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
  const [showFilters, setShowFilters] = useState(false);
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
  const activeFilters =
    (status !== "pending" ? 1 : 0) + (categoryId !== ALL ? 1 : 0) + (dueFrom ? 1 : 0) + (dueTo ? 1 : 0);
  const clearFilters = () => {
    setStatus("pending");
    setCategoryId(ALL);
    setDueFrom("");
    setDueTo("");
  };
  const categoryItems = [{ value: ALL, label: "Todas as categorias" }, ...categories.map((c) => ({ value: c.id, label: c.name }))];

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Contas a pagar e a receber</h1>
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

      {summary && <SummarySentence summary={summary} />}

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

      <div className="flex flex-wrap items-center gap-2">
        <div role="group" aria-label="Direção" className="flex gap-1">
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
        <Button
          size="sm"
          variant="outline"
          aria-expanded={showFilters}
          aria-controls="filtros"
          onClick={() => setShowFilters((value) => !value)}
        >
          {activeFilters > 0 ? `Filtros · ${activeFilters}` : "Filtros"}
        </Button>
      </div>

      {showFilters && (
        <div id="filtros" role="group" aria-label="Filtros" className="border-border bg-card flex flex-wrap items-end gap-3 rounded-xl border p-4">
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
          {activeFilters > 0 && (
            <Button size="sm" variant="ghost" onClick={clearFilters}>
              Limpar filtros
            </Button>
          )}
        </div>
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {data && (
        <>
          <CommitmentList items={data.items} accounts={accounts} categories={categories} onChanged={refresh} />
        </>
      )}
    </main>
  );
}

/** Uma frase no lugar dos cartões de resumo (doc 33, decisão 4). */
function SummarySentence({ summary }: { summary: CommitmentSummary }) {
  const { payable, receivable } = summary;
  const late = (n: number, word: string) => (n > 0 ? <>, sendo <strong className="text-expense font-semibold">{n} {word}</strong></> : null);
  return (
    <p className="text-muted-foreground text-base">
      A pagar <strong className="text-foreground font-mono font-semibold">{formatCurrency(payable.open_amount)}</strong>
      {late(payable.overdue_count, payable.overdue_count === 1 ? "vencida" : "vencidas")}. A receber{" "}
      <strong className="text-foreground font-mono font-semibold">{formatCurrency(receivable.open_amount)}</strong>
      {late(receivable.overdue_count, receivable.overdue_count === 1 ? "atrasada" : "atrasadas")}.
    </p>
  );
}
