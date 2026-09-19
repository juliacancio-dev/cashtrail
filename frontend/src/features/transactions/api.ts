import { apiClient } from "@/lib/api-client";
import type { CreateTransactionFormValues, Transaction } from "@/features/transactions/schemas";

export async function listTransactions(): Promise<Transaction[]> {
  const response = await apiClient.get("/transactions");
  if (!response.ok) throw new Error("erro ao carregar lancamentos");
  return response.json() as Promise<Transaction[]>;
}

export async function createTransaction(values: CreateTransactionFormValues): Promise<Transaction> {
  const response = await apiClient.post("/transactions", {
    ...values,
    description: values.description || null,
  });
  if (!response.ok) throw new Error("erro ao criar lancamento");
  return response.json() as Promise<Transaction>;
}
