import { apiClient } from "@/lib/api-client";
import type {
  ColumnMapping,
  ConfirmResult,
  ConfirmRow,
  PreviewResponse,
} from "@/features/statement-import/schemas";

/** O backend devolve `detail` em texto para erros de arquivo (SEC-004); outros formatos caem no fallback. */
async function errorDetail(response: Response, fallback: string): Promise<string> {
  if (response.status === 429) return "muitas tentativas, aguarde um minuto e tente de novo";
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // corpo não-JSON: usa o fallback
  }
  return fallback;
}

export async function previewImport(
  file: File,
  accountId: string,
  mapping?: ColumnMapping,
): Promise<PreviewResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("account_id", accountId);
  if (mapping) form.append("mapping", JSON.stringify(mapping));

  const response = await apiClient.postForm("/statement-imports/preview", form);
  if (!response.ok) throw new Error(await errorDetail(response, "erro ao ler o arquivo"));
  return response.json() as Promise<PreviewResponse>;
}

export async function confirmImport(payload: {
  account_id: string;
  file_name: string;
  file_sha256: string;
  rows_total: number;
  rows: ConfirmRow[];
}): Promise<ConfirmResult> {
  const response = await apiClient.post("/statement-imports", payload);
  if (!response.ok) throw new Error(await errorDetail(response, "erro ao importar os lançamentos"));
  return response.json() as Promise<ConfirmResult>;
}
