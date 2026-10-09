import { z } from "zod";

export type InvoiceStatus = "future" | "open" | "closed" | "overdue" | "paid";

export const NO_ACCOUNT = "none";

/** Rótulo em texto: a situação nunca depende só da cor. */
export const invoiceStatusLabel: Record<InvoiceStatus, string> = {
  future: "Futura",
  open: "Aberta",
  closed: "Fechada",
  overdue: "Vencida",
  paid: "Paga",
};

export type Card = {
  id: string;
  account_id: string;
  account_name: string;
  closing_day: number;
  due_day: number;
  credit_limit: string | null;
  default_payment_account_id: string | null;
  debt: string;
  available: string | null;
  over_limit: boolean;
  created_at: string;
};

export type Invoice = {
  closing_date: string;
  period_start: string;
  due_date: string;
  status: InvoiceStatus;
  total: string;
  paid: string;
  balance: string;
  previous_closing_date: string;
  next_closing_date: string;
  purchases_count: number;
};

export type Purchase = {
  transaction_id: string;
  description: string | null;
  amount: string;
  type: "income" | "expense";
  occurred_at: string;
  category_id: string;
  invoice_closing_date: string;
  moved: boolean;
};

export type Payment = {
  id: string;
  transfer_id: string;
  amount: string;
  paid_at: string;
  created_at: string;
};

export type InvoiceDetail = Invoice & { purchases: Purchase[]; payments: Payment[] };

export type CardsSummary = {
  days: number;
  overdue_count: number;
  overdue_amount: string;
  due_soon_count: number;
  due_soon_amount: string;
  debt: string;
};

const day = z
  .string()
  .refine((value) => Number.isInteger(Number(value)) && Number(value) >= 1 && Number(value) <= 31, "use um dia de 1 a 31");

export const cardFormSchema = z.object({
  account_id: z.string(),
  closing_day: day,
  due_day: day,
  credit_limit: z
    .string()
    .optional()
    .refine((value) => !value || Number(value) > 0, "o limite deve ser maior que zero"),
  default_payment_account_id: z.string(),
});

export type CardFormValues = z.infer<typeof cardFormSchema>;

export const purchaseFormSchema = z.object({
  description: z.string().min(1, "informe a descrição").max(255),
  amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  purchase_date: z.string().min(1, "informe a data"),
  category_id: z.string().min(1, "selecione uma categoria"),
  installments: z
    .string()
    .refine((value) => Number.isInteger(Number(value)) && Number(value) >= 1 && Number(value) <= 60, "use de 1 a 60"),
});

export type PurchaseFormValues = z.infer<typeof purchaseFormSchema>;

export const paymentFormSchema = z.object({
  amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  paid_at: z.string().min(1, "informe a data"),
  from_account_id: z.string().min(1, "selecione a conta de origem"),
});

export type PaymentFormValues = z.infer<typeof paymentFormSchema>;
