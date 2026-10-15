import { apiClient } from "@/lib/api-client";
import { apiFail } from "@/lib/api-errors";
import type {
  Balances,
  CashFlow,
  Dre,
  FlowColumn,
  FlowDirection,
  FlowItem,
  NetWorth,
  NetWorthPoint,
} from "@/features/reports/schemas";

export async function getBalances(): Promise<Balances> {
  const response = await apiClient.get("/reports/balances");
  if (!response.ok) return apiFail(response, "erro ao carregar os saldos");
  return response.json() as Promise<Balances>;
}

function dreQuery(startDate: string, endDate: string, includeForecast: boolean): string {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
  if (includeForecast) params.set("include_forecast", "true");
  return params.toString();
}

export async function getDre(startDate: string, endDate: string, includeForecast: boolean): Promise<Dre> {
  const response = await apiClient.get(`/reports/dre?${dreQuery(startDate, endDate, includeForecast)}`);
  if (!response.ok) return apiFail(response, "erro ao carregar o DRE");
  return response.json() as Promise<Dre>;
}

export async function getCashFlow(startMonth: string, months: number): Promise<CashFlow> {
  const response = await apiClient.get(`/reports/cash-flow?start_month=${startMonth}&months=${months}`);
  if (!response.ok) return apiFail(response, "erro ao carregar o fluxo de caixa");
  return response.json() as Promise<CashFlow>;
}

export async function getCashFlowItems(
  month: string,
  column: FlowColumn,
  direction: FlowDirection,
): Promise<FlowItem[]> {
  const params = new URLSearchParams({ month, column, direction });
  const response = await apiClient.get(`/reports/cash-flow/items?${params.toString()}`);
  if (!response.ok) return apiFail(response, "erro ao carregar os itens");
  return response.json() as Promise<FlowItem[]>;
}

/** Baixa um CSV gerado pelo backend (com o token da sessão, por isso não é um link simples). */
export async function downloadCsv(path: string, filename: string): Promise<void> {
  const response = await apiClient.get(path);
  if (!response.ok) return apiFail(response, "erro ao exportar o CSV");
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function dreCsvPath(startDate: string, endDate: string, includeForecast: boolean): string {
  return `/reports/dre.csv?${dreQuery(startDate, endDate, includeForecast)}`;
}

export function cashFlowCsvPath(startMonth: string, months: number): string {
  return `/reports/cash-flow.csv?start_month=${startMonth}&months=${months}`;
}

export async function getNetWorth(asOf?: string): Promise<NetWorth> {
  const response = await apiClient.get(`/reports/net-worth${asOf ? `?as_of=${asOf}` : ""}`);
  if (!response.ok) return apiFail(response, "erro ao carregar o balanço");
  return response.json() as Promise<NetWorth>;
}

export async function getNetWorthHistory(months: number): Promise<NetWorthPoint[]> {
  const response = await apiClient.get(`/reports/net-worth/history?months=${months}`);
  if (!response.ok) return apiFail(response, "erro ao carregar a evolução do patrimônio");
  return response.json() as Promise<NetWorthPoint[]>;
}

export function netWorthCsvPath(asOf?: string): string {
  return `/reports/net-worth.csv${asOf ? `?as_of=${asOf}` : ""}`;
}
