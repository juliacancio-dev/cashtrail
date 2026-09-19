import { apiClient } from "@/lib/api-client";
import type { Dashboard } from "@/features/dashboard/schemas";

export async function getDashboard(): Promise<Dashboard> {
  const response = await apiClient.get("/dashboard");
  if (!response.ok) throw new Error("erro ao carregar dashboard");
  return response.json() as Promise<Dashboard>;
}
