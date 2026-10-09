import { apiClient } from "@/lib/api-client";
import { apiFail as fail } from "@/lib/api-errors";
import {
  NO_ACCOUNT,
  type Commitment,
  type CommitmentDetail,
  type CommitmentFilters,
  type CommitmentFormValues,
  type CommitmentList,
  type CommitmentSummary,
  type SettleFormValues,
} from "@/features/commitments/schemas";

export async function listCommitments(filters: CommitmentFilters): Promise<CommitmentList> {
  const params = new URLSearchParams();
  if (filters.direction) params.set("direction", filters.direction);
  if (filters.status) params.set("status", filters.status);
  if (filters.due_from) params.set("due_from", filters.due_from);
  if (filters.due_to) params.set("due_to", filters.due_to);
  if (filters.category_id) params.set("category_id", filters.category_id);

  const query = params.toString();
  const response = await apiClient.get(`/commitments${query ? `?${query}` : ""}`);
  if (!response.ok) return fail(response, "erro ao carregar as contas");
  return response.json() as Promise<CommitmentList>;
}

export async function getCommitmentSummary(): Promise<CommitmentSummary> {
  const response = await apiClient.get("/commitments/summary");
  if (!response.ok) return fail(response, "erro ao carregar o resumo");
  return response.json() as Promise<CommitmentSummary>;
}

export async function getCommitment(id: string): Promise<CommitmentDetail> {
  const response = await apiClient.get(`/commitments/${id}`);
  if (!response.ok) return fail(response, "erro ao carregar a conta");
  return response.json() as Promise<CommitmentDetail>;
}

export async function createCommitments(values: CommitmentFormValues): Promise<Commitment[]> {
  const response = await apiClient.post("/commitments", {
    direction: values.direction,
    description: values.description,
    counterparty: values.counterparty || null,
    amount: values.amount,
    due_date: values.due_date,
    category_id: values.category_id,
    account_id: values.account_id === NO_ACCOUNT ? null : values.account_id,
    notes: values.notes || null,
    installments: Number(values.installments),
  });
  if (!response.ok) return fail(response, "erro ao criar a conta");
  return response.json() as Promise<Commitment[]>;
}

export async function updateCommitment(
  id: string,
  values: CommitmentFormValues,
  lockedValues: boolean,
): Promise<Commitment> {
  const body: Record<string, unknown> = {
    description: values.description,
    counterparty: values.counterparty || null,
    category_id: values.category_id,
    account_id: values.account_id === NO_ACCOUNT ? null : values.account_id,
    notes: values.notes || null,
  };
  // Pago ou cancelado não aceita mudar valor/vencimento (RB-013): nem manda.
  if (!lockedValues) {
    body.amount = values.amount;
    body.due_date = values.due_date;
  }
  const response = await apiClient.patch(`/commitments/${id}`, body);
  if (!response.ok) return fail(response, "erro ao salvar a conta");
  return response.json() as Promise<Commitment>;
}

export async function cancelCommitment(id: string): Promise<Commitment> {
  const response = await apiClient.post(`/commitments/${id}/cancel`);
  if (!response.ok) return fail(response, "erro ao cancelar a conta");
  return response.json() as Promise<Commitment>;
}

export async function settleCommitment(id: string, values: SettleFormValues): Promise<CommitmentDetail> {
  const response = await apiClient.post(`/commitments/${id}/settlements`, {
    amount: values.amount,
    paid_at: values.paid_at,
    account_id: values.account_id,
  });
  if (!response.ok) return fail(response, "erro ao registrar a baixa");
  return response.json() as Promise<CommitmentDetail>;
}

export async function undoSettlement(id: string, settlementId: string): Promise<CommitmentDetail> {
  const response = await apiClient.delete(`/commitments/${id}/settlements/${settlementId}`);
  if (!response.ok) return fail(response, "erro ao desfazer a baixa");
  return response.json() as Promise<CommitmentDetail>;
}
