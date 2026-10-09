/** O backend devolve `detail` em texto nas regras de negócio (ex: baixa acima do saldo). */
export async function apiFail(response: Response, fallback: string): Promise<never> {
  if (response.status === 429) throw new Error("muitas tentativas, aguarde um minuto");
  let detail: string | null = null;
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") detail = body.detail;
  } catch {
    // corpo não-JSON (ex: 204): usa a mensagem padrão
  }
  throw new Error(detail ?? fallback);
}
