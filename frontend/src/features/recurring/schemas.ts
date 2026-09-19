import { z } from "zod";

export const frequencyOptions = [
  { value: "weekly", label: "Semanal" },
  { value: "monthly", label: "Mensal" },
] as const;

export const createRecurringSchema = z.object({
  account_id: z.string().min(1, "selecione uma conta"),
  category_id: z.string().min(1, "selecione uma categoria"),
  type: z.enum(["income", "expense"]),
  amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  description: z.string().optional(),
  frequency: z.enum(["weekly", "monthly"]),
  next_occurrence_date: z.string().min(1, "informe a proxima data"),
});

export type CreateRecurringFormValues = z.infer<typeof createRecurringSchema>;

export type Recurring = {
  id: string;
  account_id: string;
  category_id: string;
  type: "income" | "expense";
  amount: string;
  description: string | null;
  frequency: "weekly" | "monthly";
  next_occurrence_date: string;
  is_active: boolean;
  created_at: string;
};
