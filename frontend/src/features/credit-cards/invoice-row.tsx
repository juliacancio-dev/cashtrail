"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getInvoice, movePurchase, payInvoice, undoPayment } from "@/features/credit-cards/api";
import { PaymentForm } from "@/features/credit-cards/payment-form";
import {
  invoiceStatusLabel,
  type Card,
  type Invoice,
  type InvoiceDetail,
  type InvoiceStatus,
  type PaymentFormValues,
} from "@/features/credit-cards/schemas";
import { formatCurrency, formatDate } from "@/lib/format";

type Option = { id: string; name: string; is_archived?: boolean };

const badgeClass: Record<InvoiceStatus, string> = {
  future: "bg-muted text-muted-foreground",
  open: "bg-blue-500/15 text-blue-700 dark:text-blue-400",
  closed: "bg-amber-500/15 text-amber-700 dark:text-amber-400",
  overdue: "bg-destructive/10 text-destructive",
  paid: "bg-green-600/15 text-green-700 dark:text-green-400",
};

export function InvoiceRow({
  card,
  invoice,
  accounts,
  categories,
  onChanged,
}: {
  card: Card;
  invoice: Invoice;
  accounts: Option[];
  categories: Option[];
  onChanged: () => Promise<void>;
}) {
  const [expanded, setExpanded] = useState(false);
  const [paying, setPaying] = useState(false);
  const [detail, setDetail] = useState<InvoiceDetail | null>(null);
  const [confirming, setConfirming] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Recarrega o detalhe ao abrir e sempre que a fatura mudar (total, saldo ou quantidade de compras).
  useEffect(() => {
    if (!expanded) return;
    let cancelled = false;
    getInvoice(card.id, invoice.closing_date)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar a fatura");
      });
    return () => {
      cancelled = true;
    };
  }, [expanded, card.id, invoice.closing_date, invoice.total, invoice.balance, invoice.purchases_count]);

  const categoryName = (id: string) => categories.find((c) => c.id === id)?.name ?? "-";
  const payable = invoice.status !== "future" && Number(invoice.balance) > 0;
  const activeAccounts = accounts.filter((a) => !a.is_archived && a.id !== card.account_id);

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

  return (
    <div className="flex flex-col gap-3 rounded-lg border p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium">
            Fatura que fecha em {formatDate(invoice.closing_date)}
            <span className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ${badgeClass[invoice.status]}`}>
              {invoiceStatusLabel[invoice.status]}
            </span>
          </p>
          <p className="text-muted-foreground text-sm">
            {formatDate(invoice.period_start)} a {formatDate(invoice.closing_date)} · vence em{" "}
            {formatDate(invoice.due_date)} · {invoice.purchases_count} lançamento(s)
          </p>
        </div>
        <div className="text-right">
          <p className="font-medium">{formatCurrency(invoice.total)}</p>
          {Number(invoice.paid) > 0 && (
            <p className="text-muted-foreground text-xs">
              pago {formatCurrency(invoice.paid)} · saldo {formatCurrency(invoice.balance)}
            </p>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={() => setExpanded((value) => !value)}>
          {expanded ? "Ocultar detalhes" : "Ver compras e pagamentos"}
        </Button>
        {payable && (
          <Button size="sm" onClick={() => setPaying((value) => !value)}>
            Pagar fatura
          </Button>
        )}
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {paying && (
        <PaymentForm
          invoice={invoice}
          accounts={activeAccounts}
          defaultAccountId={card.default_payment_account_id}
          onCancel={() => setPaying(false)}
          onSubmit={async (values: PaymentFormValues) => {
            await payInvoice(card.id, invoice.closing_date, values);
            setPaying(false);
            await onChanged();
          }}
        />
      )}

      {expanded && detail && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium">Compras</p>
            {detail.purchases.length === 0 && <p className="text-muted-foreground text-sm">Nenhuma compra nesta fatura.</p>}
            {detail.purchases.map((purchase) => (
              <div key={purchase.transaction_id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <span>
                  {formatDate(purchase.occurred_at)} · {purchase.description || categoryName(purchase.category_id)}
                  {purchase.moved && <span className="text-muted-foreground"> · fatura escolhida</span>}
                </span>
                <span className="flex items-center gap-2">
                  <span className={purchase.type === "income" ? "text-green-700 dark:text-green-400" : ""}>
                    {purchase.type === "income" ? "+ " : "− "}
                    {formatCurrency(purchase.amount)}
                  </span>
                  <Button
                    size="xs"
                    variant="outline"
                    aria-label="Mover para a fatura anterior"
                    onClick={() =>
                      run(() => movePurchase(card.id, purchase.transaction_id, invoice.previous_closing_date))
                    }
                  >
                    ← fatura anterior
                  </Button>
                  <Button
                    size="xs"
                    variant="outline"
                    aria-label="Mover para a fatura seguinte"
                    onClick={() => run(() => movePurchase(card.id, purchase.transaction_id, invoice.next_closing_date))}
                  >
                    fatura seguinte →
                  </Button>
                </span>
              </div>
            ))}
          </div>

          {detail.payments.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium">Pagamentos</p>
              {detail.payments.map((payment) => (
                <div key={payment.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span>
                    {formatDate(payment.paid_at)} · {formatCurrency(payment.amount)}
                  </span>
                  {confirming === payment.id ? (
                    <span className="flex gap-2">
                      <Button
                        size="xs"
                        variant="destructive"
                        onClick={() =>
                          run(
                            () => undoPayment(card.id, invoice.closing_date, payment.id),
                            () => setConfirming(null),
                          )
                        }
                      >
                        Apagar pagamento e transferência
                      </Button>
                      <Button size="xs" variant="ghost" onClick={() => setConfirming(null)}>
                        Voltar
                      </Button>
                    </span>
                  ) : (
                    <Button size="xs" variant="outline" onClick={() => setConfirming(payment.id)}>
                      Desfazer
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
