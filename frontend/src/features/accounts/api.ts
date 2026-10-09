import { apiClient } from "@/lib/api-client";
import { apiFail } from "@/lib/api-errors";
import type { Account } from "@/features/accounts/schemas";

export async function listAccounts(): Promise<Account[]> {
  const response = await apiClient.get("/accounts");
  if (!response.ok) throw new Error("erro ao carregar contas");
  return response.json() as Promise<Account[]>;
}

export async function createAccount(
  name: string,
  type: Account["type"],
  openingBalance?: string,
): Promise<Account> {
  const response = await apiClient.post("/accounts", {
    name,
    type,
    opening_balance: openingBalance ? openingBalance : "0",
  });
  if (!response.ok) throw new Error("erro ao criar conta");
  return response.json() as Promise<Account>;
}

export async function updateOpeningBalance(id: string, openingBalance: string): Promise<Account> {
  const response = await apiClient.patch(`/accounts/${id}`, { opening_balance: openingBalance });
  if (!response.ok) return apiFail(response, "erro ao salvar o saldo inicial");
  return response.json() as Promise<Account>;
}

export async function archiveAccount(id: string): Promise<Account> {
  const response = await apiClient.post(`/accounts/${id}/archive`);
  if (!response.ok) throw new Error("erro ao arquivar conta");
  return response.json() as Promise<Account>;
}
