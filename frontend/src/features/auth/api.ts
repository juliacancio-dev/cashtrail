import { apiClient } from "@/lib/api-client";

const TOO_MANY_ATTEMPTS = "muitas tentativas, aguarde um minuto e tente de novo";

export async function requestPasswordReset(email: string): Promise<void> {
  const response = await apiClient.post("/auth/forgot-password", { email });
  if (response.status === 429) throw new Error(TOO_MANY_ATTEMPTS);
  if (!response.ok) throw new Error("erro ao solicitar redefinição de senha");
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  const response = await apiClient.post("/auth/reset-password", {
    token,
    new_password: newPassword,
  });
  if (response.status === 429) throw new Error(TOO_MANY_ATTEMPTS);
  if (response.status === 400) {
    throw new Error("este link é inválido ou expirou — peça um novo");
  }
  if (!response.ok) throw new Error("erro ao redefinir a senha");
}
