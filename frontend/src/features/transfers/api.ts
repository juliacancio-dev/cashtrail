import { apiClient } from "@/lib/api-client";
import { apiFail } from "@/lib/api-errors";
import type { Transfer, TransferFormValues } from "@/features/transfers/schemas";

export async function listTransfers(): Promise<Transfer[]> {
  const response = await apiClient.get("/transfers");
  if (!response.ok) return apiFail(response, "erro ao carregar as transferências");
  return response.json() as Promise<Transfer[]>;
}

export async function createTransfer(values: TransferFormValues): Promise<Transfer> {
  const response = await apiClient.post("/transfers", {
    ...values,
    description: values.description || null,
  });
  if (!response.ok) return apiFail(response, "erro ao criar a transferência");
  return response.json() as Promise<Transfer>;
}

export async function deleteTransfer(id: string): Promise<void> {
  const response = await apiClient.delete(`/transfers/${id}`);
  if (!response.ok) return apiFail(response, "erro ao desfazer a transferência");
}
