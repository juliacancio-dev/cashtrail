import { z } from "zod";

export type Transfer = {
  id: string;
  from_account_id: string;
  to_account_id: string;
  amount: string;
  occurred_at: string;
  description: string | null;
  created_at: string;
};

export const transferFormSchema = z
  .object({
    from_account_id: z.string().min(1, "selecione a conta de origem"),
    to_account_id: z.string().min(1, "selecione a conta de destino"),
    amount: z
      .string()
      .min(1, "informe um valor")
      .refine((value) => Number(value) > 0, "o valor deve ser maior que zero"),
    occurred_at: z.string().min(1, "informe a data"),
    description: z.string().max(255).optional(),
  })
  .refine((values) => values.from_account_id !== values.to_account_id, {
    message: "origem e destino devem ser contas diferentes",
    path: ["to_account_id"],
  });

export type TransferFormValues = z.infer<typeof transferFormSchema>;
