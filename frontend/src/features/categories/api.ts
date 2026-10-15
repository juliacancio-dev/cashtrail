import { apiClient } from "@/lib/api-client";
import { apiFail } from "@/lib/api-errors";
import { NO_GROUP, NO_IR_KIND, type Category } from "@/features/categories/schemas";

export async function listCategories(): Promise<Category[]> {
  const response = await apiClient.get("/categories");
  if (!response.ok) throw new Error("erro ao carregar categorias");
  return response.json() as Promise<Category[]>;
}

export async function createCategory(name: string, dreGroup: string = NO_GROUP): Promise<Category> {
  const response = await apiClient.post("/categories", {
    name,
    dre_group: dreGroup === NO_GROUP ? null : dreGroup,
  });
  if (!response.ok) throw new Error("erro ao criar categoria");
  return response.json() as Promise<Category>;
}

export async function updateCategoryGroup(id: string, dreGroup: string): Promise<Category> {
  const response = await apiClient.patch(`/categories/${id}`, {
    dre_group: dreGroup === NO_GROUP ? null : dreGroup,
  });
  if (!response.ok) return apiFail(response, "erro ao salvar o grupo");
  return response.json() as Promise<Category>;
}

export async function updateCategoryIrKind(id: string, irKind: string): Promise<Category> {
  const response = await apiClient.patch(`/categories/${id}`, {
    ir_kind: irKind === NO_IR_KIND ? null : irKind,
  });
  if (!response.ok) return apiFail(response, "erro ao salvar a marca fiscal");
  return response.json() as Promise<Category>;
}

export async function archiveCategory(id: string): Promise<Category> {
  const response = await apiClient.post(`/categories/${id}/archive`);
  if (!response.ok) throw new Error("erro ao arquivar categoria");
  return response.json() as Promise<Category>;
}
