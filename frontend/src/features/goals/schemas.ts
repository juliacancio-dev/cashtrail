import { z } from "zod";

export const createGoalSchema = z.object({
  name: z.string().min(1, "informe um nome"),
  target_amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  target_date: z.string().optional(),
});

export type CreateGoalFormValues = z.infer<typeof createGoalSchema>;

export const contributionSchema = z.object({
  account_id: z.string().min(1, "selecione uma conta"),
  category_id: z.string().min(1, "selecione uma categoria"),
  type: z.enum(["income", "expense"]),
  amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
  occurred_at: z.string().min(1, "informe uma data"),
});

export type ContributionFormValues = z.infer<typeof contributionSchema>;

export type Goal = {
  id: string;
  name: string;
  target_amount: string;
  target_date: string | null;
  is_achieved: boolean;
  current_amount: string;
  percent_achieved: string;
  created_at: string;
};
