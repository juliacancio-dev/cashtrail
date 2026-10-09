export type AccountKind = "checking" | "savings" | "credit_card" | "loan";

export type AccountBalance = {
  account_id: string;
  name: string;
  type: AccountKind;
  is_archived: boolean;
  opening_balance: string;
  balance: string;
};

export type Balances = {
  accounts: AccountBalance[];
  cash_total: string;
  card_debt_total: string;
  loan_debt_total: string;
};

export type DreCategory = { category_id: string | null; name: string; amount: string };

export type DreLine = {
  key: string;
  label: string;
  kind: "group" | "subtotal" | "ungrouped";
  amount: string;
  previous_amount: string;
  percent_of_net_revenue: string | null;
  categories: DreCategory[];
};

export type Dre = {
  start_date: string;
  end_date: string;
  previous_start_date: string;
  previous_end_date: string;
  include_forecast: boolean;
  lines: DreLine[];
  net_result: string;
  previous_net_result: string;
  ungrouped_count: number;
};

export type SourceTotals = {
  planned_in: string;
  planned_out: string;
  realized_in: string;
  realized_out: string;
};

export type CashFlowMonth = {
  month: string;
  status: "past" | "current" | "future";
  opening_balance: string;
  planned_in: string;
  planned_out: string;
  realized_in: string;
  realized_out: string;
  projected_in: string;
  projected_out: string;
  closing_projected: string;
  closing_realized: string | null;
  variance_in: string;
  variance_out: string;
  sources: Record<string, SourceTotals>;
};

export type CashFlow = {
  start_month: string;
  months: CashFlowMonth[];
  cash_balance_today: string;
  warnings: string[];
};

export type FlowColumn = "planned" | "realized" | "projected";
export type FlowDirection = "in" | "out";

export type FlowItem = {
  column: "realized" | "planned";
  direction: FlowDirection;
  when: string;
  amount: string;
  source: string;
  description: string;
  category_id: string | null;
  category_name: string | null;
};

export const sourceLabels: Record<string, string> = {
  transactions: "Lançamentos",
  transfers: "Pagamento de cartão",
  commitments: "Contas a pagar/receber",
  card_invoices: "Faturas de cartão",
  recurring: "Recorrências",
};
