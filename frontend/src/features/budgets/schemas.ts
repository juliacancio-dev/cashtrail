import { z } from "zod";

export const createBudgetSchema = z.object({
  category_id: z.string().min(1, "selecione uma categoria"),
  month: z.string().min(1, "informe o mes"),
  limit_amount: z
    .string()
    .min(1, "informe um valor")
    .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
});

export type CreateBudgetFormValues = z.infer<typeof createBudgetSchema>;

export type Budget = {
  id: string;
  category_id: string;
  category_name: string;
  month: string;
  limit_amount: string;
  spent_amount: string;
  percent_consumed: string;
  is_exceeded: boolean;
};
