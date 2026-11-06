import { apiClient } from "@/lib/api-client";
import type { CreateTransactionFormValues, Transaction } from "@/features/transactions/schemas";
import { monthBounds } from "@/lib/format";

/** Lançamentos de um mês ("2026-11"); sem mês, todos. */
export async function listTransactions(month?: string): Promise<Transaction[]> {
  const query = month ? `?start_date=${monthBounds(month)[0]}&end_date=${monthBounds(month)[1]}` : "";
  const response = await apiClient.get(`/transactions${query}`);
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
