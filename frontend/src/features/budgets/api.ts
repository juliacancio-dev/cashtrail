import { apiClient } from "@/lib/api-client";
import type { Budget, CreateBudgetFormValues } from "@/features/budgets/schemas";

export async function listBudgets(): Promise<Budget[]> {
  const response = await apiClient.get("/budgets");
  if (!response.ok) throw new Error("erro ao carregar orcamentos");
  return response.json() as Promise<Budget[]>;
}

export async function createBudget(values: CreateBudgetFormValues): Promise<Budget> {
  const response = await apiClient.post("/budgets", values);
  if (!response.ok) {
    if (response.status === 409) throw new Error("ja existe orcamento para essa categoria e mes");
    throw new Error("erro ao criar orcamento");
  }
  return response.json() as Promise<Budget>;
}

export async function deleteBudget(id: string): Promise<void> {
  const response = await apiClient.delete(`/budgets/${id}`);
  if (!response.ok) throw new Error("erro ao excluir orcamento");
}
