"use client";

import { useEffect, useState } from "react";

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
  const [open, setOpen] = useState(true);
  const [mode, setMode] = useState<Mode>(null);
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
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
  }, [open, card.id, reloadKey, card.debt]);

  async function changed() {
    setReloadKey((key) => key + 1);
    await onCardChanged();
  }

  const used = Number(card.debt);
  const limit = card.credit_limit ? Number(card.credit_limit) : null;
  const percent = limit ? Math.min(Math.max((used / limit) * 100, 0), 100) : 0;
  const activeAccounts = accounts.filter((a) => !a.is_archived && a.id !== card.account_id);
  const activeCategories = categories.filter((c) => !c.is_archived);

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
              <div className={card.over_limit ? "bg-destructive h-full" : "h-full bg-green-600"} style={{ width: `${percent}%` }} />
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
          <Button size="sm" variant="outline" onClick={() => setMode(mode === "edit" ? null : "edit")}>
            Editar cartão
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setOpen((value) => !value)}>
            {open ? "Ocultar faturas" : "Mostrar faturas"}
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

        {open && invoices && (
          <div className="flex flex-col gap-3">
            {invoices.map((invoice) => (
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
      </CardContent>
    </UiCard>
  );
}
