import { apiClient } from "@/lib/api-client";
import { apiFail as fail } from "@/lib/api-errors";
import {
  NO_ACCOUNT,
  type AmortizationMode,
  type AmortizationPreview,
  type Debt,
  type DebtDetail,
  type DebtFormValues,
  type DebtsSummary,
  type Installment,
  type SchedulePreview,
} from "@/features/debts/schemas";

function scheduleBody(values: DebtFormValues) {
  return {
    principal: values.principal,
    installments: Number(values.installments),
    first_due_date: values.first_due_date,
    system: values.system,
    monthly_rate: values.system === "zero" || values.monthly_rate === "" ? "0" : values.monthly_rate,
  };
}

export async function previewSchedule(values: DebtFormValues): Promise<SchedulePreview> {
  const response = await apiClient.post("/debts/preview", scheduleBody(values));
  if (!response.ok) return fail(response, "erro ao simular o cronograma");
  return response.json() as Promise<SchedulePreview>;
}

export async function listDebts(): Promise<Debt[]> {
  const response = await apiClient.get("/debts");
  if (!response.ok) return fail(response, "erro ao carregar as dividas");
  return response.json() as Promise<Debt[]>;
}

export async function getDebtsSummary(): Promise<DebtsSummary> {
  const response = await apiClient.get("/debts/summary");
  if (!response.ok) return fail(response, "erro ao carregar o resumo de dividas");
  return response.json() as Promise<DebtsSummary>;
}

export async function getDebt(id: string): Promise<DebtDetail> {
  const response = await apiClient.get(`/debts/${id}`);
  if (!response.ok) return fail(response, "erro ao carregar a divida");
  return response.json() as Promise<DebtDetail>;
}

export async function createDebt(values: DebtFormValues): Promise<DebtDetail> {
  const response = await apiClient.post("/debts", {
    ...scheduleBody(values),
    name: values.name,
    creditor: values.creditor || null,
    contracted_at: values.contracted_at,
    interest_category_id: values.interest_category_id,
    payment_account_id: values.payment_account_id === NO_ACCOUNT ? null : values.payment_account_id,
    received_account_id: values.received_account_id === NO_ACCOUNT ? null : values.received_account_id,
  });
  if (!response.ok) return fail(response, "erro ao cadastrar a divida");
  return response.json() as Promise<DebtDetail>;
}

export async function payInstallment(
  debtId: string,
  installmentId: string,
  paidAt: string,
  accountId: string,
): Promise<Installment> {
  const response = await apiClient.post(`/debts/${debtId}/installments/${installmentId}/payment`, {
    paid_at: paidAt || null,
    account_id: accountId === NO_ACCOUNT || accountId === "" ? null : accountId,
  });
  if (!response.ok) return fail(response, "erro ao pagar a parcela");
  return response.json() as Promise<Installment>;
}

export async function undoInstallmentPayment(debtId: string, installmentId: string): Promise<Installment> {
  const response = await apiClient.delete(`/debts/${debtId}/installments/${installmentId}/payment`);
  if (!response.ok) return fail(response, "erro ao desfazer o pagamento");
  return response.json() as Promise<Installment>;
}

export async function updateInstallment(
  debtId: string,
  installmentId: string,
  changes: { amount?: string; due_date?: string },
): Promise<Installment> {
  const response = await apiClient.patch(`/debts/${debtId}/installments/${installmentId}`, changes);
  if (!response.ok) return fail(response, "erro ao salvar a parcela");
  return response.json() as Promise<Installment>;
}

export async function previewAmortization(
  debtId: string,
  amount: string,
  mode: AmortizationMode,
): Promise<AmortizationPreview> {
  const response = await apiClient.post(`/debts/${debtId}/amortization-preview`, {
    amount: mode === "payoff" ? null : amount,
    mode,
  });
  if (!response.ok) return fail(response, "erro ao simular a amortizacao");
  return response.json() as Promise<AmortizationPreview>;
}

export async function amortize(
  debtId: string,
  amount: string,
  mode: AmortizationMode,
  paidAt: string,
  accountId: string,
): Promise<DebtDetail> {
  const response = await apiClient.post(`/debts/${debtId}/amortizations`, {
    amount: mode === "payoff" ? null : amount,
    mode,
    paid_at: paidAt || null,
    account_id: accountId === NO_ACCOUNT || accountId === "" ? null : accountId,
  });
  if (!response.ok) return fail(response, "erro ao registrar a amortizacao");
  return response.json() as Promise<DebtDetail>;
}
