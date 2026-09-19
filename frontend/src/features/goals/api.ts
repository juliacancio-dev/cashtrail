import { apiClient } from "@/lib/api-client";
import type { ContributionFormValues, CreateGoalFormValues, Goal } from "@/features/goals/schemas";

export async function listGoals(): Promise<Goal[]> {
  const response = await apiClient.get("/goals");
  if (!response.ok) throw new Error("erro ao carregar metas");
  return response.json() as Promise<Goal[]>;
}

export async function createGoal(values: CreateGoalFormValues): Promise<Goal> {
  const response = await apiClient.post("/goals", {
    ...values,
    target_date: values.target_date || null,
  });
  if (!response.ok) throw new Error("erro ao criar meta");
  return response.json() as Promise<Goal>;
}

export async function deleteGoal(id: string): Promise<void> {
  const response = await apiClient.delete(`/goals/${id}`);
  if (!response.ok) throw new Error("erro ao excluir meta");
}

export async function contributeToGoal(goalId: string, values: ContributionFormValues): Promise<void> {
  const response = await apiClient.post(`/goals/${goalId}/contributions`, values);
  if (!response.ok) throw new Error("erro ao registrar contribuicao");
}

export async function getGoal(goalId: string): Promise<Goal> {
  const response = await apiClient.get(`/goals/${goalId}`);
  if (!response.ok) throw new Error("erro ao carregar meta");
  return response.json() as Promise<Goal>;
}
