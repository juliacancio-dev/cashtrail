import { z } from "zod";

export const NO_ACCOUNT = "none";

export const systemOptions = [
  { value: "price", label: "Price (parcelas iguais)" },
  { value: "sac", label: "SAC (amortização constante)" },
  { value: "zero", label: "Sem juros (parcelas iguais)" },
] as const;

export type DebtSystem = (typeof systemOptions)[number]["value"];

export const amortizationModeOptions = [
  { value: "reduce_term", label: "Reduzir o prazo (mantém a parcela)" },
  { value: "reduce_installment", label: "Reduzir a parcela (mantém o prazo)" },
] as const;

export type AmortizationMode = "reduce_term" | "reduce_installment" | "payoff";

export type InstallmentStatus =
  | "open"
  | "due_today"
  | "overdue"
  | "paid"
  | "canceled"
  | "superseded"
  | "partially_paid";

const positiveNumber = (message: string) =>
  z.string().refine((value) => Number.isFinite(Number(value)) && Number(value) > 0, message);

export const debtFormSchema = z.object({
  name: z.string().min(1, "informe um nome"),
  creditor: z.string().optional(),
  principal: positiveNumber("informe o valor"),
  contracted_at: z.string().min(1, "informe a data"),
  installments: z
    .string()
    .refine((value) => Number.isInteger(Number(value)) && Number(value) >= 1 && Number(value) <= 360, "de 1 a 360"),
  first_due_date: z.string().min(1, "informe o primeiro vencimento"),
  system: z.enum(["price", "sac", "zero"]),
  monthly_rate: z
    .string()
    .refine((value) => value === "" || (Number.isFinite(Number(value)) && Number(value) >= 0), "informe a taxa"),
  interest_category_id: z.string().min(1, "escolha a categoria dos juros"),
  payment_account_id: z.string(),
  received_account_id: z.string(),
});

export type DebtFormValues = z.infer<typeof debtFormSchema>;

export type PlannedInstallment = {
  number: number;
  due_date: string;
  principal: string;
  charges: string;
  amount: string;
  balance: string;
};

export type SchedulePreview = {
  rows: PlannedInstallment[];
  total_paid: string;
  total_charges: string;
};

export type Installment = {
  id: string;
  number: number;
  commitment_id: string;
  due_date: string;
  amount: string;
  principal_part: string;
  charges: string;
  status: InstallmentStatus;
  paid: boolean;
};

export type Amortization = {
  id: string;
  amount: string;
  paid_at: string;
  mode: string;
  created_at: string;
};

export type NextInstallment = {
  id: string;
  number: number;
  due_date: string;
  amount: string;
  status: InstallmentStatus;
};

export type Debt = {
  id: string;
  account_id: string;
  name: string;
  creditor: string | null;
  principal: string;
  contracted_at: string;
  installments: number;
  system: DebtSystem;
  monthly_rate: string;
  first_due_date: string;
  payment_account_id: string | null;
  interest_category_id: string;
  outstanding: string;
  principal_paid: string;
  charges_paid: string;
  charges_projected: string;
  installments_paid: number;
  installments_open: number;
  next_installment: NextInstallment | null;
  is_paid_off: boolean;
};

export type DebtDetail = Debt & {
  installment_list: Installment[];
  amortizations: Amortization[];
  settlement_ids: Record<string, string>;
};

export type AmortizationPreview = {
  outstanding_before: string;
  outstanding_after: string;
  installments_before: number;
  installments_after: number;
  charges_before: string;
  charges_after: string;
  rows: PlannedInstallment[];
};

export type DebtsSummary = {
  outstanding_total: string;
  active_count: number;
  overdue_count: number;
  next_due_date: string | null;
  next_amount: string | null;
  next_debt_name: string | null;
};

export function systemLabel(system: DebtSystem): string {
  return systemOptions.find((option) => option.value === system)?.label ?? system;
}

export const installmentStatusLabel: Record<InstallmentStatus, string> = {
  open: "em aberto",
  due_today: "vence hoje",
  overdue: "atrasada",
  paid: "paga",
  canceled: "cancelada",
  superseded: "recalculada",
  partially_paid: "paga em parte",
};
