import { z } from "zod";

export const registerSchema = z.object({
  email: z.string().email("e-mail invalido"),
  password: z.string().min(8, "a senha precisa ter pelo menos 8 caracteres"),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z.string().email("e-mail invalido"),
  password: z.string().min(1, "informe a senha"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const forgotPasswordSchema = z.object({
  email: z.string().email("e-mail invalido"),
});

export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    newPassword: z.string().min(8, "a senha precisa ter pelo menos 8 caracteres"),
    confirmPassword: z.string(),
  })
  .refine((values) => values.newPassword === values.confirmPassword, {
    message: "as senhas não conferem",
    path: ["confirmPassword"],
  });

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;
