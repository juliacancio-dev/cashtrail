import { apiClient } from "@/lib/api-client";
import type { Account } from "@/features/accounts/schemas";

export async function listAccounts(): Promise<Account[]> {
  const response = await apiClient.get("/accounts");
  if (!response.ok) throw new Error("erro ao carregar contas");
  return response.json() as Promise<Account[]>;
}

export async function createAccount(name: string, type: Account["type"]): Promise<Account> {
  const response = await apiClient.post("/accounts", { name, type });
  if (!response.ok) throw new Error("erro ao criar conta");
  return response.json() as Promise<Account>;
}

export async function archiveAccount(id: string): Promise<Account> {
  const response = await apiClient.post(`/accounts/${id}/archive`);
  if (!response.ok) throw new Error("erro ao arquivar conta");
  return response.json() as Promise<Account>;
}
