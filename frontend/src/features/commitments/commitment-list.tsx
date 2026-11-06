"use client";

import { useState } from "react";

import { ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  cancelCommitment,
  getCommitment,
  settleCommitment,
  undoSettlement,
  updateCommitment,
} from "@/features/commitments/api";
import { CommitmentForm } from "@/features/commitments/commitment-form";
import { SettleForm } from "@/features/commitments/settle-form";
import {
  statusLabel,
  type Commitment,
  type CommitmentFormValues,
  type CommitmentStatus,
  type Settlement,
  type SettleFormValues,
} from "@/features/commitments/schemas";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";

type Option = { id: string; name: string; is_archived?: boolean };
type Mode = "settle" | "edit" | "history" | null;

const active = (options: Option[]) => options.filter((option) => !option.is_archived);

const badgeClass: Record<CommitmentStatus, string> = {
  open: "bg-muted text-muted-foreground",
  due_today: "bg-warning/12 text-warning",
  overdue: "bg-destructive/10 text-destructive",
  partially_paid: "bg-info/12 text-info",
  paid: "bg-income/12 text-income",
  canceled: "bg-muted text-muted-foreground line-through",
};

const WEEKDAYS = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];

/** Dias entre duas datas ISO, sem passar por fuso. */
function daysBetween(from: string, to: string): number {
  const utc = (iso: string) => {
    const [y, m, d] = iso.split("-").map(Number);
    return Date.UTC(y, m - 1, d);
  };
  return Math.round((utc(to) - utc(from)) / 86_400_000);
}

/** "hoje", "amanhã", "sexta, 06/11" nesta semana; senão a data. */
function dueLabel(iso: string): string {
  const diff = daysBetween(todayIso(), iso);
  if (diff === 0) return "hoje";
  if (diff === 1) return "amanhã";
  if (diff === -1) return "ontem";
  const [y, m, d] = iso.split("-").map(Number);
  if (diff > 1 && diff < 7) return `${WEEKDAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()]}, ${String(d).padStart(2, "0")}/${String(m).padStart(2, "0")}`;
  return y === new Date().getFullYear() ? formatDate(iso).slice(0, 5) : formatDate(iso);
}

const GROUPS = ["Vencidas", "Próximos 7 dias", "Mais tarde", "Encerradas"] as const;

function groupOf(c: Commitment): (typeof GROUPS)[number] {
  if (c.status === "paid" || c.status === "canceled") return "Encerradas";
  if (c.status === "overdue") return "Vencidas";
  return daysBetween(todayIso(), c.due_date) <= 7 ? "Próximos 7 dias" : "Mais tarde";
}

function CommitmentRow({
  commitment,
  accounts,
  categories,
  onChanged,
}: {
  commitment: Commitment;
  accounts: Option[];
  categories: Option[];
  onChanged: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>(null);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [confirming, setConfirming] = useState<"cancel" | string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const payable = commitment.direction === "payable";
  const pending = commitment.status !== "paid" && commitment.status !== "canceled";
  const locked = !pending;
  const hasPayments = Number(commitment.paid_amount) > 0;
  const categoryName = categories.find((c) => c.id === commitment.category_id)?.name ?? "-";
  const accountName = accounts.find((a) => a.id === commitment.account_id)?.name;

  async function run(action: () => Promise<unknown>, after?: () => void) {
    setError(null);
    try {
      await action();
      after?.();
      await onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "algo deu errado");
    }
  }

  async function openHistory() {
    if (mode === "history") return setMode(null);
    setError(null);
    try {
      setSettlements((await getCommitment(commitment.id)).settlements);
      setMode("history");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao carregar o histórico");
    }
  }

  const detailsId = `conta-${commitment.id}`;
  const showChip = commitment.status !== "open";

  return (
    <li className="border-border border-b">
      <div className="flex items-center gap-3 py-2.5">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-controls={detailsId}
          className="hover:bg-muted -mx-1.5 flex min-h-11 min-w-0 flex-1 items-center gap-2.5 rounded-lg px-1.5 text-left transition-colors"
        >
          <ChevronRight
            aria-hidden="true"
            className={`text-muted-foreground size-4 shrink-0 transition-transform motion-reduce:transition-none ${open ? "rotate-90" : ""}`}
          />
          <span className="min-w-0">
            <span className="block truncate">
              {commitment.description}
              {commitment.installment_number && (
                <span className="text-muted-foreground">
                  {" "}
                  · parcela {commitment.installment_number}/{commitment.installment_count}
                </span>
              )}
            </span>
            <span className="text-muted-foreground block truncate text-[13px]">
              {commitment.status === "overdue" ? "venceu" : "vence"} {dueLabel(commitment.due_date)} · {categoryName}
              {hasPayments && pending && ` · ${payable ? "pago" : "recebido"} ${formatCurrency(commitment.paid_amount)}`}
            </span>
          </span>
        </button>
        {showChip && (
          <span className={`hidden shrink-0 rounded-full px-2 py-0.5 text-xs font-medium sm:inline-block ${badgeClass[commitment.status]}`}>
            {statusLabel(commitment.status, commitment.direction)}
          </span>
        )}
        <span className={`shrink-0 font-mono ${payable ? "" : "text-income"}`}>
          {payable ? "− " : "+ "}
          {formatCurrency(commitment.amount)}
        </span>
        {pending && (
          <Button
            size="sm"
            className="shrink-0"
            onClick={() => {
              setOpen(true);
              setMode(mode === "settle" ? null : "settle");
            }}
          >
            {payable ? "Pagar" : "Receber"}
          </Button>
        )}
      </div>

      {open && (
        <div id={detailsId} className="flex flex-col gap-3 pb-4 pl-7">
          <p className="text-muted-foreground text-sm">
            {payable ? "A pagar" : "A receber"} · {categoryName}
            {accountName && ` · ${accountName}`}
            {commitment.counterparty && ` · ${commitment.counterparty}`}
            {commitment.recurring_transaction_id && " · recorrente"}
            {hasPayments && pending && ` · saldo ${formatCurrency(commitment.balance)}`}
          </p>
          {showChip && (
            <span className={`w-fit rounded-full px-2 py-0.5 text-xs font-medium sm:hidden ${badgeClass[commitment.status]}`}>
              {statusLabel(commitment.status, commitment.direction)}
            </span>
          )}
          {commitment.notes && <p className="text-muted-foreground text-sm">{commitment.notes}</p>}

          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" variant="outline" onClick={() => setMode(mode === "edit" ? null : "edit")}>
              Editar
            </Button>
            {hasPayments && (
              <Button size="sm" variant="outline" onClick={openHistory}>
                Baixas ({settlements.length > 0 ? settlements.length : "ver"})
              </Button>
            )}
            {pending &&
              (confirming === "cancel" ? (
                <>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => run(() => cancelCommitment(commitment.id), () => setConfirming(null))}
                  >
                    Confirmar cancelamento
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setConfirming(null)}>
                    Voltar
                  </Button>
                </>
              ) : (
                <Button size="sm" variant="ghost" className="text-expense" onClick={() => setConfirming("cancel")}>
                  Cancelar conta
                </Button>
              ))}
          </div>
        {error && <p className="text-destructive text-sm">{error}</p>}

        {mode === "settle" && (
          <SettleForm
            commitment={commitment}
            accounts={active(accounts)}
            onCancel={() => setMode(null)}
            onSubmit={async (values: SettleFormValues) =>
              run(() => settleCommitment(commitment.id, values), () => setMode(null))
            }
          />
        )}

        {mode === "edit" && (
          <CommitmentForm
            accounts={active(accounts)}
            categories={active(categories)}
            initial={commitment}
            lockValues={locked}
            onCancel={() => setMode(null)}
            onSubmit={async (values: CommitmentFormValues) =>
              run(() => updateCommitment(commitment.id, values, locked), () => setMode(null))
            }
          />
        )}

        {mode === "history" && (
          <div className="flex flex-col gap-2 rounded-md border bg-muted/30 p-3">
            {settlements.length === 0 && <p className="text-muted-foreground text-sm">Nenhuma baixa.</p>}
            {settlements.map((settlement) => (
              <div key={settlement.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <span>
                  {formatDate(settlement.paid_at)} · {formatCurrency(settlement.amount)}
                </span>
                {confirming === settlement.id ? (
                  <span className="flex gap-2">
                    <Button
                      size="xs"
                      variant="destructive"
                      onClick={() =>
                        run(
                          async () => {
                            const detail = await undoSettlement(commitment.id, settlement.id);
                            setSettlements(detail.settlements);
                          },
                          () => setConfirming(null),
                        )
                      }
                    >
                      Apagar baixa e lançamento
                    </Button>
                    <Button size="xs" variant="ghost" onClick={() => setConfirming(null)}>
                      Voltar
                    </Button>
                  </span>
                ) : (
                  <Button size="xs" variant="outline" onClick={() => setConfirming(settlement.id)}>
                    Desfazer
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
        </div>
      )}
    </li>
  );
}

export function CommitmentList({
  items,
  accounts,
  categories,
  onChanged,
}: {
  items: Commitment[];
  accounts: Option[];
  categories: Option[];
  onChanged: () => Promise<void>;
}) {
  if (items.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma conta encontrada para este filtro.</p>;
  }

  // Agrupadas por vencimento (doc 33, decisão 4), cada grupo do vencimento mais próximo para o mais distante.
  const groups = GROUPS.map((name) => ({
    name,
    items: items.filter((c) => groupOf(c) === name).sort((a, b) => a.due_date.localeCompare(b.due_date)),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="flex flex-col gap-6">
      {groups.map((group) => (
        <section key={group.name} aria-labelledby={`grupo-${group.name}`}>
          <h2 id={`grupo-${group.name}`} className="mb-1.5 flex items-baseline gap-2 text-[15px] font-medium">
            {group.name}{" "}
            <span className="text-muted-foreground text-[13px] font-normal">{group.items.length}</span>
          </h2>
          <ul className="border-border border-t">
            {group.items.map((commitment) => (
              <CommitmentRow
                key={commitment.id}
                commitment={commitment}
                accounts={accounts}
                categories={categories}
                onChanged={onChanged}
              />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
