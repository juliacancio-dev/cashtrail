import { apiClient } from "@/lib/api-client";
import { apiFail } from "@/lib/api-errors";
import {
  NO_ACCOUNT,
  type Card,
  type CardFormValues,
  type CardsSummary,
  type Invoice,
  type InvoiceDetail,
  type PaymentFormValues,
  type Purchase,
  type PurchaseFormValues,
} from "@/features/credit-cards/schemas";

export async function listCards(): Promise<Card[]> {
  const response = await apiClient.get("/cards");
  if (!response.ok) return apiFail(response, "erro ao carregar os cartões");
  return response.json() as Promise<Card[]>;
}

export async function getCardsSummary(): Promise<CardsSummary> {
  const response = await apiClient.get("/cards/summary");
  if (!response.ok) return apiFail(response, "erro ao carregar o resumo dos cartões");
  return response.json() as Promise<CardsSummary>;
}

export async function createCard(values: CardFormValues): Promise<Card> {
  const response = await apiClient.post("/cards", {
    account_id: values.account_id,
    closing_day: Number(values.closing_day),
    due_day: Number(values.due_day),
    credit_limit: values.credit_limit || null,
    default_payment_account_id: values.default_payment_account_id === NO_ACCOUNT ? null : values.default_payment_account_id,
  });
  if (!response.ok) return apiFail(response, "erro ao configurar o cartão");
  return response.json() as Promise<Card>;
}

export async function updateCard(id: string, values: CardFormValues): Promise<Card> {
  const response = await apiClient.patch(`/cards/${id}`, {
    closing_day: Number(values.closing_day),
    due_day: Number(values.due_day),
    credit_limit: values.credit_limit || null,
    default_payment_account_id: values.default_payment_account_id === NO_ACCOUNT ? null : values.default_payment_account_id,
  });
  if (!response.ok) return apiFail(response, "erro ao salvar o cartão");
  return response.json() as Promise<Card>;
}

export async function listInvoices(cardId: string): Promise<Invoice[]> {
  const response = await apiClient.get(`/cards/${cardId}/invoices`);
  if (!response.ok) return apiFail(response, "erro ao carregar as faturas");
  return response.json() as Promise<Invoice[]>;
}

export async function getInvoice(cardId: string, closingDate: string): Promise<InvoiceDetail> {
  const response = await apiClient.get(`/cards/${cardId}/invoices/${closingDate}`);
  if (!response.ok) return apiFail(response, "erro ao carregar a fatura");
  return response.json() as Promise<InvoiceDetail>;
}

export async function createPurchase(cardId: string, values: PurchaseFormValues): Promise<Purchase[]> {
  const response = await apiClient.post(`/cards/${cardId}/purchases`, {
    description: values.description,
    amount: values.amount,
    purchase_date: values.purchase_date,
    category_id: values.category_id,
    installments: Number(values.installments),
  });
  if (!response.ok) return apiFail(response, "erro ao registrar a compra");
  return response.json() as Promise<Purchase[]>;
}

export async function movePurchase(cardId: string, transactionId: string, closingDate: string): Promise<Purchase> {
  const response = await apiClient.patch(`/cards/${cardId}/purchases/${transactionId}`, {
    invoice_closing_date: closingDate,
  });
  if (!response.ok) return apiFail(response, "erro ao mover a compra");
  return response.json() as Promise<Purchase>;
}

export async function payInvoice(cardId: string, closingDate: string, values: PaymentFormValues): Promise<InvoiceDetail> {
  const response = await apiClient.post(`/cards/${cardId}/invoices/${closingDate}/payments`, {
    amount: values.amount,
    paid_at: values.paid_at,
    from_account_id: values.from_account_id,
  });
  if (!response.ok) return apiFail(response, "erro ao pagar a fatura");
  return response.json() as Promise<InvoiceDetail>;
}

export async function undoPayment(cardId: string, closingDate: string, paymentId: string): Promise<InvoiceDetail> {
  const response = await apiClient.delete(`/cards/${cardId}/invoices/${closingDate}/payments/${paymentId}`);
  if (!response.ok) return apiFail(response, "erro ao desfazer o pagamento");
  return response.json() as Promise<InvoiceDetail>;
}
