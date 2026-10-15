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

/** Marca fiscal da despesa (Marco 14): só o que reduz a base do IRPF. "none" = sem efeito fiscal. */
export type IrKind = "deduction_health" | "deduction_education" | "deduction_pension";
export const NO_IR_KIND = "none";

export const irKindOptions = [
  { value: NO_IR_KIND, label: "Sem efeito no IR" },
  { value: "deduction_health", label: "Saúde (dedutível)" },
  { value: "deduction_education", label: "Educação (dedutível, com limite)" },
  { value: "deduction_pension", label: "Previdência PGBL (até 12%)" },
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
  ir_kind: IrKind | null;
  is_archived: boolean;
  created_at: string;
};
