import { apiClient } from "@/lib/api-client";
import type { CreateRecurringFormValues, Recurring } from "@/features/recurring/schemas";

export async function listRecurring(): Promise<Recurring[]> {
  const response = await apiClient.get("/recurring");
  if (!response.ok) throw new Error("erro ao carregar recorrencias");
  return response.json() as Promise<Recurring[]>;
}

export async function createRecurring(values: CreateRecurringFormValues): Promise<Recurring> {
  const response = await apiClient.post("/recurring", {
    ...values,
    description: values.description || null,
  });
  if (!response.ok) throw new Error("erro ao criar recorrencia");
  return response.json() as Promise<Recurring>;
}

export async function deactivateRecurring(id: string): Promise<Recurring> {
  const response = await apiClient.post(`/recurring/${id}/deactivate`);
  if (!response.ok) throw new Error("erro ao desativar recorrencia");
  return response.json() as Promise<Recurring>;
}
