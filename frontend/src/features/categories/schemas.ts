import { z } from "zod";

export type DreGroup =
  | "revenue"
  | "deduction"
  | "variable_expense"
  | "fixed_expense"
  | "financial_expense"
  | "financial_revenue";

/** Valor do campo quando a categoria não tem grupo (o backend guarda `null`). */
export const NO_GROUP = "none";

export const dreGroupOptions = [
  { value: NO_GROUP, label: "Sem grupo" },
  { value: "revenue", label: "Receitas" },
  { value: "deduction", label: "Deduções" },
  { value: "variable_expense", label: "Despesas variáveis" },
  { value: "fixed_expense", label: "Despesas fixas" },
  { value: "financial_expense", label: "Despesas financeiras" },
  { value: "financial_revenue", label: "Receitas financeiras" },
] as const;

export function dreGroupLabel(group: DreGroup | null): string {
  return dreGroupOptions.find((option) => option.value === (group ?? NO_GROUP))?.label ?? "Sem grupo";
}

export const createCategorySchema = z.object({
  name: z.string().min(1, "informe um nome"),
  dre_group: z.string(),
});

export type CreateCategoryFormValues = z.infer<typeof createCategorySchema>;

export type Category = {
  id: string;
  name: string;
  dre_group: DreGroup | null;
  is_archived: boolean;
  created_at: string;
};
