import { z } from "zod";

export const accountTypeOptions = [
  { value: "checking", label: "Conta corrente" },
  { value: "savings", label: "Poupança" },
  { value: "credit_card", label: "Cartão de crédito" },
] as const;

export const createAccountSchema = z.object({
  name: z.string().min(1, "informe um nome"),
  type: z.enum(["checking", "savings", "credit_card"]),
});

export type CreateAccountFormValues = z.infer<typeof createAccountSchema>;

export type Account = {
  id: string;
  name: string;
  type: "checking" | "savings" | "credit_card";
  is_archived: boolean;
  created_at: string;
};
