import { z } from "zod";

export type Direction = "payable" | "receivable";
export type CommitmentStatus =
  | "open"
  | "due_today"
  | "overdue"
  | "partially_paid"
  | "paid"
  | "canceled";
export type StatusFilter = "pending" | CommitmentStatus;

export const directionOptions = [
  { value: "payable", label: "A pagar" },
  { value: "receivable", label: "A receber" },
] as const;

export const statusFilterOptions = [
  { value: "pending", label: "Em aberto (com saldo)" },
  { value: "overdue", label: "Atrasados" },
  { value: "due_today", label: "Vencem hoje" },
  { value: "partially_paid", label: "Pagos parcialmente" },
  { value: "paid", label: "Quitados" },
  { value: "canceled", label: "Cancelados" },
  { value: "all", label: "Todos" },
] as const;

/** Rótulo em texto: a situação nunca depende só da cor. */
export function statusLabel(status: CommitmentStatus, direction: Direction): string {
  const labels: Record<CommitmentStatus, string> = {
    open: "Em aberto",
    due_today: "Vence hoje",
    overdue: "Atrasado",
    partially_paid: direction === "payable" ? "Pago em parte" : "Recebido em parte",
    paid: direction === "payable" ? "Pago" : "Recebido",
    canceled: "Cancelado",
  };
  return labels[status];
}

export type Settlement = {
  id: string;
  commitment_id: string;
  transaction_id: string;
  amount: string;
  paid_at: string;
  created_at: string;
};

export type Commitment = {
  id: string;
  direction: Direction;
  description: string;
  counterparty: string | null;
  amount: string;
  due_date: string;
  category_id: string;
  account_id: string | null;
  notes: string | null;
  installment_group_id: string | null;
  installment_number: number | null;
  installment_count: number | null;
  is_canceled: boolean;
  created_at: string;
  paid_amount: string;
  balance: string;
  status: CommitmentStatus;
};

export type CommitmentDetail = Commitment & { settlements: Settlement[] };

export type CommitmentList = {
  items: Commitment[];
  totals: { count: number; payable_balance: string; receivable_balance: string };
};

export type DirectionSummary = {
  overdue_count: number;
  overdue_amount: string;
  due_soon_count: number;
  due_soon_amount: string;
  open_amount: string;
};

export type CommitmentSummary = {
  days: number;
  payable: DirectionSummary;
  receivable: DirectionSummary;
};

export type CommitmentFilters = {
  direction?: Direction;
  status?: StatusFilter;
  due_from?: string;
  due_to?: string;
  category_id?: string;
};

export const NO_ACCOUNT = "none";

export const commitmentFormSchema = z.object({
  direction: z.enum(["payable", "receivable"]),
  description: z.string().min(1, "informe a descrição").max(255),
  counterparty: z.string().max(255).optional(),
  amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  due_date: z.string().min(1, "informe o vencimento"),
  category_id: z.string().min(1, "selecione uma categoria"),
  account_id: z.string(),
  notes: z.string().max(1000).optional(),
  installments: z
    .string()
    .refine(
      (value) => Number.isInteger(Number(value)) && Number(value) >= 1 && Number(value) <= 120,
      "use um número de 1 a 120",
    ),
});

export type CommitmentFormValues = z.infer<typeof commitmentFormSchema>;

export const settleFormSchema = z.object({
  amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  paid_at: z.string().min(1, "informe a data"),
  account_id: z.string().min(1, "selecione a conta"),
});

export type SettleFormValues = z.infer<typeof settleFormSchema>;
