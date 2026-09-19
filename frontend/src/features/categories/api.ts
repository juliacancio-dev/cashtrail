import { apiClient } from "@/lib/api-client";
import type { Category } from "@/features/categories/schemas";

export async function listCategories(): Promise<Category[]> {
  const response = await apiClient.get("/categories");
  if (!response.ok) throw new Error("erro ao carregar categorias");
  return response.json() as Promise<Category[]>;
}

export async function createCategory(name: string): Promise<Category> {
  const response = await apiClient.post("/categories", { name });
  if (!response.ok) throw new Error("erro ao criar categoria");
  return response.json() as Promise<Category>;
}

export async function archiveCategory(id: string): Promise<Category> {
  const response = await apiClient.post(`/categories/${id}/archive`);
  if (!response.ok) throw new Error("erro ao arquivar categoria");
  return response.json() as Promise<Category>;
}
