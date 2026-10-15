import { apiClient } from "@/lib/api-client";
import { apiFail as fail } from "@/lib/api-errors";
import {
  NO_ASSET,
  type InsuranceSummary,
  type Policy,
  type PolicyFormValues,
} from "@/features/insurance/schemas";

export async function listPolicies(): Promise<Policy[]> {
  const response = await apiClient.get("/insurance");
  if (!response.ok) return fail(response, "erro ao carregar as apólices");
  return response.json() as Promise<Policy[]>;
}

export async function getInsuranceSummary(): Promise<InsuranceSummary> {
  const response = await apiClient.get("/insurance/summary");
  if (!response.ok) return fail(response, "erro ao carregar o resumo de seguros");
  return response.json() as Promise<InsuranceSummary>;
}

export async function createPolicy(values: PolicyFormValues): Promise<Policy> {
  const response = await apiClient.post("/insurance", {
    kind: values.kind,
    insurer: values.insurer,
    name: values.name,
    premium_amount: values.premium_amount,
    premium_frequency: values.premium_frequency,
    coverage_amount: values.coverage_amount || null,
    renews_on: values.renews_on,
    first_due_on: values.premium_frequency === "monthly" ? values.first_due_on || null : null,
    asset_id: values.asset_id === NO_ASSET ? null : values.asset_id,
    payment_account_id: values.payment_account_id,
    category_id: values.category_id,
  });
  if (!response.ok) return fail(response, "erro ao cadastrar a apólice");
  return response.json() as Promise<Policy>;
}

export async function renewPolicy(id: string, premium: string): Promise<Policy> {
  const response = await apiClient.post(`/insurance/${id}/renew`, { premium_amount: premium || null });
  if (!response.ok) return fail(response, "erro ao renovar a apólice");
  return response.json() as Promise<Policy>;
}

export async function deactivatePolicy(id: string): Promise<Policy> {
  const response = await apiClient.post(`/insurance/${id}/deactivate`);
  if (!response.ok) return fail(response, "erro ao encerrar a apólice");
  return response.json() as Promise<Policy>;
}
