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
