"use client";

import { useEffect, useState } from "react";
import { ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card as UiCard, CardContent } from "@/components/ui/card";
import { createPurchase, listInvoices, updateCard } from "@/features/credit-cards/api";
import { CardForm } from "@/features/credit-cards/card-form";
import { InvoiceRow } from "@/features/credit-cards/invoice-row";
import { PurchaseForm } from "@/features/credit-cards/purchase-form";
import type { Card, CardFormValues, Invoice, PurchaseFormValues } from "@/features/credit-cards/schemas";
import { formatCurrency } from "@/lib/format";

type Option = { id: string; name: string; is_archived?: boolean };
type Mode = "purchase" | "edit" | null;

export function CardPanel({
  card,
  accounts,
  categories,
  onCardChanged,
}: {
  card: Card;
  accounts: Option[];
  categories: Option[];
  onCardChanged: () => Promise<void>;
}) {
  const [mode, setMode] = useState<Mode>(null);
  const [showOthers, setShowOthers] = useState(false);
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listInvoices(card.id)
      .then((data) => {
        if (!cancelled) setInvoices(data);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar as faturas");
      });
    return () => {
      cancelled = true;
    };
  }, [card.id, reloadKey, card.debt]);

  async function changed() {
    setReloadKey((key) => key + 1);
    await onCardChanged();
  }

  const used = Number(card.debt);
  const limit = card.credit_limit ? Number(card.credit_limit) : null;
  const percent = limit ? Math.min(Math.max((used / limit) * 100, 0), 100) : 0;
  const activeAccounts = accounts.filter((a) => !a.is_archived && a.id !== card.account_id);
  const activeCategories = categories.filter((c) => !c.is_archived);

  // Fatura atual (doc 33, decisão 5): a fechada ainda não paga mais antiga (a mais urgente); se não houver, a aberta.
  const byClosing = [...(invoices ?? [])].sort((a, b) => a.closing_date.localeCompare(b.closing_date));
  const unpaidClosed = byClosing.find((i) => (i.status === "overdue" || i.status === "closed") && Number(i.balance) > 0);
  const current = unpaidClosed ?? byClosing.find((i) => i.status === "open") ?? null;
  const others = (invoices ?? []).filter((i) => i !== current);
  const othersId = `faturas-${card.id}`;

  return (
    <UiCard>
      <CardContent className="flex flex-col gap-4 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-lg font-medium">{card.account_name}</p>
            <p className="text-muted-foreground text-sm">
              Fecha dia {card.closing_day} · vence dia {card.due_day}
            </p>
          </div>
          <div className="text-right">
            <p className="text-muted-foreground text-sm">Dívida do cartão</p>
            <p className="text-xl font-semibold">{formatCurrency(card.debt)}</p>
          </div>
        </div>

        {limit !== null && (
          <div className="flex flex-col gap-1">
            <div className="bg-muted h-2 w-full overflow-hidden rounded-full">
              <div className={card.over_limit ? "bg-destructive h-full" : "h-full bg-income"} style={{ width: `${percent}%` }} />
            </div>
            <p className={`text-sm ${card.over_limit ? "text-destructive font-medium" : "text-muted-foreground"}`}>
              {card.over_limit
                ? `Acima do limite em ${formatCurrency(Math.abs(Number(card.available)))} (limite ${formatCurrency(limit)})`
                : `Disponível ${formatCurrency(card.available ?? 0)} de ${formatCurrency(limit)}`}
            </p>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={() => setMode(mode === "purchase" ? null : "purchase")}>
            Nova compra
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setMode(mode === "edit" ? null : "edit")}>
            Editar cartão
          </Button>
        </div>

        {error && <p className="text-destructive text-sm">{error}</p>}

        {mode === "purchase" && (
          <PurchaseForm
            categories={activeCategories}
            onCancel={() => setMode(null)}
            onSubmit={async (values: PurchaseFormValues) => {
              await createPurchase(card.id, values);
              setMode(null);
              await changed();
            }}
          />
        )}

        {mode === "edit" && (
          <CardForm
            cardAccounts={[]}
            paymentAccounts={activeAccounts}
            initial={card}
            onCancel={() => setMode(null)}
            onSubmit={async (values: CardFormValues) => {
              await updateCard(card.id, values);
              setMode(null);
              await changed();
            }}
          />
        )}

        {current && (
          <InvoiceRow card={card} invoice={current} accounts={accounts} categories={categories} onChanged={changed} />
        )}
        {invoices && !current && others.length === 0 && (
          <p className="text-muted-foreground text-sm">Nenhuma fatura ainda. Registre uma compra para começar.</p>
        )}

        {others.length > 0 && (
          <div className="flex flex-col gap-3">
            <button
              type="button"
              aria-expanded={showOthers}
              aria-controls={othersId}
              onClick={() => setShowOthers((value) => !value)}
              className="text-muted-foreground hover:text-foreground flex min-h-11 w-fit items-center gap-1.5 text-sm"
            >
              <ChevronRight
                aria-hidden="true"
                className={`size-4 transition-transform motion-reduce:transition-none ${showOthers ? "rotate-90" : ""}`}
              />
              Faturas anteriores e futuras · {others.length}
            </button>
            {showOthers && (
              <div id={othersId} className="flex flex-col gap-3">
                {others.map((invoice) => (
                  <InvoiceRow
                    key={invoice.closing_date}
                    card={card}
                    invoice={invoice}
                    accounts={accounts}
                    categories={categories}
                    onChanged={changed}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </UiCard>
  );
}
