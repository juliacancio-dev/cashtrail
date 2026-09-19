import { z } from "zod";

export const transactionTypeOptions = [
  { value: "income", label: "Receita" },
  { value: "expense", label: "Despesa" },
] as const;

export const createTransactionSchema = z.object({
  account_id: z.string().min(1, "selecione uma conta"),
  category_id: z.string().min(1, "selecione uma categoria"),
  type: z.enum(["income", "expense"]),
  amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  description: z.string().optional(),
  occurred_at: z.string().min(1, "informe uma data"),
});

export type CreateTransactionFormValues = z.infer<typeof createTransactionSchema>;

export type Transaction = {
  id: string;
  account_id: string;
  category_id: string;
  type: "income" | "expense";
  amount: string;
  description: string | null;
  occurred_at: string;
  created_at: string;
};
