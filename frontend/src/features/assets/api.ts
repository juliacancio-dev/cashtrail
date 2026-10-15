import { apiClient } from "@/lib/api-client";
import { apiFail as fail } from "@/lib/api-errors";
import {
  NO_DEBT,
  type Asset,
  type AssetDetail,
  type AssetFormValues,
} from "@/features/assets/schemas";

export async function listAssets(): Promise<Asset[]> {
  const response = await apiClient.get("/assets");
  if (!response.ok) return fail(response, "erro ao carregar os bens");
  return response.json() as Promise<Asset[]>;
}

export async function getAsset(id: string): Promise<AssetDetail> {
  const response = await apiClient.get(`/assets/${id}`);
  if (!response.ok) return fail(response, "erro ao carregar o bem");
  return response.json() as Promise<AssetDetail>;
}

export async function createAsset(values: AssetFormValues): Promise<AssetDetail> {
  const response = await apiClient.post("/assets", {
    name: values.name,
    kind: values.kind,
    acquired_at: values.acquired_at || null,
    acquisition_value: values.acquisition_value || null,
    current_value: values.current_value,
    valued_at: values.valued_at,
    debt_id: values.debt_id === NO_DEBT ? null : values.debt_id,
  });
  if (!response.ok) return fail(response, "erro ao cadastrar o bem");
  return response.json() as Promise<AssetDetail>;
}

export async function updateAsset(
  id: string,
  changes: { name?: string; debt_id?: string | null; disposed_at?: string | null },
): Promise<AssetDetail> {
  const response = await apiClient.patch(`/assets/${id}`, changes);
  if (!response.ok) return fail(response, "erro ao salvar o bem");
  return response.json() as Promise<AssetDetail>;
}

export async function addValuation(
  id: string,
  valuedAt: string,
  value: string,
  note: string,
): Promise<AssetDetail> {
  const response = await apiClient.post(`/assets/${id}/valuations`, {
    valued_at: valuedAt,
    value,
    note: note || null,
  });
  if (!response.ok) return fail(response, "erro ao registrar a avaliação");
  return response.json() as Promise<AssetDetail>;
}

export async function deleteValuation(id: string, valuationId: string): Promise<AssetDetail> {
  const response = await apiClient.delete(`/assets/${id}/valuations/${valuationId}`);
  if (!response.ok) return fail(response, "erro ao remover a avaliação");
  return response.json() as Promise<AssetDetail>;
}
