import { apiClient } from "@/lib/api-client";
import type { Dashboard } from "@/features/dashboard/schemas";
import { monthBounds } from "@/lib/format";

/** Resumo de um mês ("2026-11"); sem mês, o backend usa o mês atual. */
export async function getDashboard(month?: string): Promise<Dashboard> {
  const query = month ? `?start_date=${monthBounds(month)[0]}&end_date=${monthBounds(month)[1]}` : "";
  const response = await apiClient.get(`/dashboard${query}`);
  if (!response.ok) throw new Error("erro ao carregar dashboard");
  return response.json() as Promise<Dashboard>;
}
