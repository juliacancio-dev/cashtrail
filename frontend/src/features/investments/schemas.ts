import { z } from "zod";

export const assetClassOptions = [
  { value: "stock", label: "Ação" },
  { value: "fii", label: "Fundo imobiliário (FII)" },
  { value: "etf", label: "ETF" },
  { value: "bdr", label: "BDR" },
  { value: "fixed_income", label: "Renda fixa (CDB, LCI, LCA)" },
  { value: "treasury", label: "Tesouro Direto" },
  { value: "fund", label: "Fundo de investimento" },
  { value: "crypto", label: "Cripto" },
  { value: "other", label: "Outro" },
] as const;

export type AssetClass = (typeof assetClassOptions)[number]["value"];

export const quoteSourceOptions = [
  { value: "brapi", label: "Automática (ações, FIIs, ETFs)" },
  { value: "manual", label: "Manual (informo o valor)" },
] as const;

export type QuoteSource = "brapi" | "manual";

export function classLabel(value: string): string {
  return assetClassOptions.find((option) => option.value === value)?.label ?? value;
}

export const assetFormSchema = z
  .object({
    account_id: z.string().min(1, "escolha a conta de investimento"),
    name: z.string().min(1, "informe um nome"),
    symbol: z.string().optional(),
    asset_class: z.enum(["stock", "fii", "etf", "bdr", "fixed_income", "treasury", "fund", "crypto", "other"]),
    quote_source: z.enum(["brapi", "manual"]),
  })
  .refine((values) => values.quote_source !== "brapi" || !!values.symbol?.trim(), {
    message: "cotação automática precisa do símbolo (ex: PETR4)",
    path: ["symbol"],
  });

export type AssetFormValues = z.infer<typeof assetFormSchema>;

export type OperationKind = "buy" | "sell" | "income" | "adjust";

export type Operation = {
  id: string;
  kind: OperationKind;
  occurred_at: string;
  quantity: string;
  unit_price: string;
  fees: string;
  amount: string;
  cost_basis: string | null;
  gain: string | null;
  cash_account_id: string | null;
  category_id: string | null;
  note: string | null;
  created_at: string;
};

export type Position = {
  id: string;
  account_id: string;
  name: string;
  symbol: string | null;
  asset_class: AssetClass;
  quote_source: QuoteSource;
  is_archived: boolean;
  quantity: string;
  avg_cost: string;
  cost: string;
  price: string | null;
  price_date: string | null;
  price_source: string | null;
  market_value: string;
  has_quote: boolean;
  is_stale_quote: boolean;
  unrealized: string;
  unrealized_pct: string | null;
  invested: string;
  proceeds: string;
  income: string;
  realized: string;
  total_return: string;
  total_return_pct: string | null;
  first_buy: string | null;
};

export type PositionDetail = Position & { operations: Operation[] };

export type PortfolioTotals = {
  market_value: string;
  cost: string;
  unrealized: string;
  invested: string;
  income: string;
  realized: string;
  total_return: string;
  total_return_pct: string | null;
};

export type Portfolio = { positions: Position[]; totals: PortfolioTotals; warnings: string[] };

export type Refresh = {
  updated: string[];
  failed: string[];
  skipped_for_cap: string[];
  requests_this_month: number;
  monthly_cap: number;
};

export type Benchmark = {
  since: string | null;
  invested: string;
  portfolio_return_pct: string | null;
  cdi_return_pct: string | null;
  difference_pct: string | null;
  note: string;
};

export const operationLabels: Record<OperationKind, string> = {
  buy: "Compra",
  sell: "Venda",
  income: "Provento",
  adjust: "Ajuste de quantidade",
};
