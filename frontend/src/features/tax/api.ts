import { apiClient } from "@/lib/api-client";
import { apiFail as fail } from "@/lib/api-errors";
import type { Dossier, StatementKind, Years } from "@/features/tax/schemas";

export async function getTaxYears(): Promise<Years> {
  const response = await apiClient.get("/tax/years");
  if (!response.ok) return fail(response, "erro ao carregar os anos");
  return response.json() as Promise<Years>;
}

export async function getDossier(year: number): Promise<Dossier> {
  const response = await apiClient.get(`/tax/${year}`);
  if (!response.ok) return fail(response, "erro ao carregar o IRPF do ano");
  return response.json() as Promise<Dossier>;
}

export async function setDependents(year: number, count: number): Promise<Dossier> {
  const response = await apiClient.put(`/tax/${year}/dependents`, { count });
  if (!response.ok) return fail(response, "erro ao salvar os dependentes");
  return response.json() as Promise<Dossier>;
}

export async function addStatement(
  year: number,
  input: {
    payer_name: string;
    kind: StatementKind;
    gross_income: string;
    social_security: string;
    withheld_tax: string;
    note: string | null;
  },
): Promise<Dossier> {
  const response = await apiClient.post(`/tax/${year}/statements`, input);
  if (!response.ok) return fail(response, "erro ao salvar o informe");
  return response.json() as Promise<Dossier>;
}

export async function deleteStatement(year: number, id: string): Promise<Dossier> {
  const response = await apiClient.delete(`/tax/${year}/statements/${id}`);
  if (!response.ok) return fail(response, "erro ao remover o informe");
  return response.json() as Promise<Dossier>;
}

export function taxCsvPath(year: number): string {
  return `/tax/${year}/export.csv`;
}
