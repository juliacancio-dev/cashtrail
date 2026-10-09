"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { formatCurrency, formatDate } from "@/lib/format";

type Option = { id: string; name: string; is_archived?: boolean };
type Mode = "settle" | "edit" | "history" | null;

const active = (options: Option[]) => options.filter((option) => !option.is_archived);

const badgeClass: Record<CommitmentStatus, string> = {
  open: "bg-muted text-muted-foreground",
  due_today: "bg-amber-500/15 text-amber-700 dark:text-amber-400",
  overdue: "bg-destructive/10 text-destructive",
  partially_paid: "bg-blue-500/15 text-blue-700 dark:text-blue-400",
  paid: "bg-green-600/15 text-green-700 dark:text-green-400",
  canceled: "bg-muted text-muted-foreground line-through",
};

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
  const [mode, setMode] = useState<Mode>(null);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [confirming, setConfirming] = useState<"cancel" | string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const payable = commitment.direction === "payable";
  const open = commitment.status !== "paid" && commitment.status !== "canceled";
  const locked = !open;
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

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium">
              {commitment.description}
              {commitment.installment_number && (
                <span className="text-muted-foreground font-normal">
                  {" "}
                  · parcela {commitment.installment_number}/{commitment.installment_count}
                </span>
              )}
            </p>
            <p className="text-muted-foreground text-sm">
              {payable ? "A pagar" : "A receber"} · vence em {formatDate(commitment.due_date)} · {categoryName}
              {commitment.counterparty && ` · ${commitment.counterparty}`}
              {accountName && ` · ${accountName}`}
              {commitment.recurring_transaction_id && " · recorrente"}
            </p>
            {commitment.notes && <p className="text-muted-foreground text-sm">{commitment.notes}</p>}
          </div>

          <div className="text-right">
            <p className={`font-medium ${payable ? "" : "text-green-700 dark:text-green-400"}`}>
              {payable ? "− " : "+ "}
              {formatCurrency(commitment.amount)}
            </p>
            {hasPayments && commitment.status !== "canceled" && commitment.status !== "paid" && (
              <p className="text-muted-foreground text-xs">
                {payable ? "pago" : "recebido"} {formatCurrency(commitment.paid_amount)} · saldo{" "}
                {formatCurrency(commitment.balance)}
              </p>
            )}
            <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${badgeClass[commitment.status]}`}>
              {statusLabel(commitment.status, commitment.direction)}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {open && (
            <Button size="sm" onClick={() => setMode(mode === "settle" ? null : "settle")}>
              {payable ? "Pagar" : "Receber"}
            </Button>
          )}
          <Button size="sm" variant="outline" onClick={() => setMode(mode === "edit" ? null : "edit")}>
            Editar
          </Button>
          {hasPayments && (
            <Button size="sm" variant="outline" onClick={openHistory}>
              Baixas ({settlements.length > 0 ? settlements.length : "ver"})
            </Button>
          )}
          {open &&
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
              <Button size="sm" variant="ghost" onClick={() => setConfirming("cancel")}>
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
      </CardContent>
    </Card>
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

  return (
    <div className="flex flex-col gap-3">
      {items.map((commitment) => (
        <CommitmentRow
          key={commitment.id}
          commitment={commitment}
          accounts={accounts}
          categories={categories}
          onChanged={onChanged}
        />
      ))}
    </div>
  );
}
