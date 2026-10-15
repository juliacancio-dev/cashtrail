export type StatementKind =
  | "salary"
  | "other_taxable"
  | "thirteenth"
  | "plr"
  | "exclusive_other"
  | "exempt";

export const statementKindOptions: { value: StatementKind; label: string; hint: string }[] = [
  { value: "salary", label: "Salário (tributável)", hint: "Rendimentos tributáveis do informe: salário, bônus pago na folha, férias." },
  { value: "other_taxable", label: "Outro rendimento tributável", hint: "Aluguel, autônomo com retenção, etc." },
  { value: "thirteenth", label: "13º salário (exclusivo na fonte)", hint: "Tributado na fonte; fora da base do ajuste anual." },
  { value: "plr", label: "PLR (exclusivo na fonte)", hint: "Participação nos lucros: tributação própria na fonte." },
  { value: "exclusive_other", label: "Rendimento financeiro (exclusivo na fonte)", hint: "CDB, Tesouro, fundos: o banco retém o imposto." },
  { value: "exempt", label: "Rendimento isento", hint: "LCI, LCA, poupança; benefícios que o informe lista como isentos." },
];

export function kindLabel(kind: StatementKind): string {
  return statementKindOptions.find((option) => option.value === kind)?.label ?? kind;
}

export type Statement = {
  id: string;
  year: number;
  payer_name: string;
  kind: StatementKind;
  gross_income: string;
  social_security: string;
  withheld_tax: string;
  note: string | null;
  created_at: string;
};

export type Modality = {
  name: string;
  deductions: string;
  base: string;
  tax_before_reducer: string;
  reducer: string;
  tax_due: string;
  balance: string;
};

export type Estimate = {
  taxable_income: string;
  social_security: string;
  withheld_tax: string;
  health: string;
  education_declared: string;
  education_deducted: string;
  pension_declared: string;
  pension_deducted: string;
  dependents: number;
  dependents_deduction: string;
  complete: Modality;
  simplified: Modality;
  best: string;
  notes: string[];
};

export type VariableMonth = {
  month: string;
  modality: "stock" | "fii";
  sales: string;
  gain: string;
  exempt: boolean;
  loss_used: string;
  loss_carried: string;
  taxable_gain: string;
  tax: string;
  irrf: string;
  darf_amount: string;
  darf_carried: string;
  due_date: string;
};

export type Right = { group: string; name: string; amount: string; note: string | null };

export type Dossier = {
  year: number;
  as_of: string;
  disclaimer: string;
  parameters: {
    year: number;
    label: string;
    consulted_at: string;
    sources: { topic: string; url: string; kind: string }[];
    unverified: string[];
    dependent_deduction: string;
    education_limit_per_person: string;
    simplified_limit: string;
    stock_exempt_monthly_sales: string;
    darf_code: string;
  };
  dependents: number;
  statements: Statement[];
  totals_by_kind: Record<StatementKind, { gross: string; social_security: string; withheld: string }>;
  estimate: Estimate;
  variable_income: VariableMonth[];
  day_trade_flags: string[];
  assets_and_rights: Right[];
  debts: Right[];
  untagged_expense_categories: number;
  warnings: string[];
};

export type Years = { years: number[]; default_year: number };
