import { apiClient } from "@/lib/api-client";
import { apiFail as fail } from "@/lib/api-errors";
import type {
  AssetFormValues,
  Benchmark,
  OperationKind,
  Portfolio,
  Position,
  PositionDetail,
  Refresh,
} from "@/features/investments/schemas";

export async function getPortfolio(): Promise<Portfolio> {
  const response = await apiClient.get("/investments");
  if (!response.ok) return fail(response, "erro ao carregar a carteira");
  return response.json() as Promise<Portfolio>;
}

export async function getBenchmark(): Promise<Benchmark> {
  const response = await apiClient.get("/investments/benchmark");
  if (!response.ok) return fail(response, "erro ao carregar o comparativo");
  return response.json() as Promise<Benchmark>;
}

export async function getInvestment(id: string): Promise<PositionDetail> {
  const response = await apiClient.get(`/investments/assets/${id}`);
  if (!response.ok) return fail(response, "erro ao carregar o ativo");
  return response.json() as Promise<PositionDetail>;
}

export async function createInvestment(values: AssetFormValues): Promise<Position> {
  const response = await apiClient.post("/investments/assets", {
    account_id: values.account_id,
    name: values.name,
    symbol: values.symbol?.trim() ? values.symbol.trim() : null,
    asset_class: values.asset_class,
    quote_source: values.quote_source,
  });
  if (!response.ok) return fail(response, "erro ao cadastrar o ativo");
  return response.json() as Promise<Position>;
}

export async function archiveInvestment(id: string, archived: boolean): Promise<Position> {
  const response = await apiClient.patch(`/investments/assets/${id}`, { is_archived: archived });
  if (!response.ok) return fail(response, "erro ao salvar o ativo");
  return response.json() as Promise<Position>;
}

export type OperationInput = {
  kind: OperationKind;
  occurred_at: string;
  quantity?: string;
  unit_price?: string;
  fees?: string;
  amount?: string;
  cash_account_id?: string | null;
  category_id?: string | null;
  note?: string | null;
};

export async function addOperation(id: string, input: OperationInput): Promise<PositionDetail> {
  const response = await apiClient.post(`/investments/assets/${id}/operations`, input);
  if (!response.ok) return fail(response, "erro ao registrar a operação");
  return response.json() as Promise<PositionDetail>;
}

export async function undoOperation(id: string, operationId: string): Promise<PositionDetail> {
  const response = await apiClient.delete(`/investments/assets/${id}/operations/${operationId}`);
  if (!response.ok) return fail(response, "erro ao desfazer a operação");
  return response.json() as Promise<PositionDetail>;
}

export async function setQuote(id: string, price: string, quotedOn: string): Promise<PositionDetail> {
  const response = await apiClient.post(`/investments/assets/${id}/quote`, { price, quoted_on: quotedOn });
  if (!response.ok) return fail(response, "erro ao registrar o valor");
  return response.json() as Promise<PositionDetail>;
}

export async function refreshQuotes(): Promise<Refresh> {
  const response = await apiClient.post("/investments/refresh");
  if (!response.ok) return fail(response, "erro ao atualizar as cotações");
  return response.json() as Promise<Refresh>;
}
