import { apiClient } from "@/lib/api-client";
import { apiFail as fail } from "@/lib/api-errors";

export type Plan = {
  current_age: number;
  target_age: number;
  monthly_income_wanted: string;
  public_benefit_monthly: string;
  real_return_annual: string;
  withdrawal_rate: string;
  monthly_contribution: string;
  include_assets: boolean;
  updated_at: string;
};

export type Scenario = {
  withdrawal_rate: string;
  real_return: string;
  target: string;
  months: number | null;
  age: string | null;
  is_base: boolean;
};

export type Result = {
  target: string;
  progress_pct: string;
  sustainable_income_today: string;
  months_to_target: number | null;
  age_at_target: string | null;
  reaches_by_target_age: boolean;
  required_contribution: string;
  gap: string;
  scenarios: Scenario[];
};

export type Overview = {
  disclaimer: string;
  plan: Plan | null;
  invested_wealth: string;
  assets_wealth: string;
  counted_wealth: string;
  result: Result | null;
  ipca_12m_pct: string | null;
  defaults: { withdrawal_rate: string; real_return_annual: string };
  warnings: string[];
};

export type PlanInput = Omit<Plan, "updated_at">;

export async function getRetirement(): Promise<Overview> {
  const response = await apiClient.get("/retirement");
  if (!response.ok) return fail(response, "erro ao carregar o plano");
  return response.json() as Promise<Overview>;
}

export async function savePlan(input: PlanInput): Promise<Overview> {
  const response = await apiClient.put("/retirement", input);
  if (!response.ok) return fail(response, "erro ao salvar o plano");
  return response.json() as Promise<Overview>;
}
