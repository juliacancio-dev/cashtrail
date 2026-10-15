import { z } from "zod";

export const NO_ASSET = "none";

export const policyKindOptions = [
  { value: "life", label: "Vida" },
  { value: "health", label: "Saúde" },
  { value: "auto", label: "Automóvel" },
  { value: "home", label: "Residencial" },
  { value: "travel", label: "Viagem" },
  { value: "other", label: "Outro" },
] as const;

export const frequencyOptions = [
  { value: "monthly", label: "Mensal" },
  { value: "annual", label: "Anual" },
] as const;

export type PolicyKind = (typeof policyKindOptions)[number]["value"];
export type PremiumFrequency = (typeof frequencyOptions)[number]["value"];

export function kindLabel(kind: string): string {
  return policyKindOptions.find((option) => option.value === kind)?.label ?? kind;
}

export const policyFormSchema = z.object({
  kind: z.enum(["life", "health", "auto", "home", "travel", "other"]),
  insurer: z.string().min(1, "informe a seguradora"),
  name: z.string().min(1, "informe um nome"),
  premium_amount: z.string().refine((v) => Number.isFinite(Number(v)) && Number(v) > 0, "informe o prêmio"),
  premium_frequency: z.enum(["monthly", "annual"]),
  coverage_amount: z
    .string()
    .optional()
    .refine((v) => !v || (Number.isFinite(Number(v)) && Number(v) >= 0), "informe um valor"),
  renews_on: z.string().min(1, "informe a renovação"),
  first_due_on: z.string().optional(),
  asset_id: z.string(),
  payment_account_id: z.string().min(1, "escolha a conta"),
  category_id: z.string().min(1, "escolha a categoria"),
});

export type PolicyFormValues = z.infer<typeof policyFormSchema>;

export type RenewalStatus = "ok" | "soon" | "overdue" | "inactive";

export type Policy = {
  id: string;
  kind: PolicyKind;
  insurer: string;
  name: string;
  premium_amount: string;
  premium_frequency: PremiumFrequency;
  coverage_amount: string | null;
  starts_on: string | null;
  renews_on: string;
  first_due_on: string | null;
  asset_id: string | null;
  payment_account_id: string;
  category_id: string;
  recurring_id: string | null;
  commitment_id: string | null;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  days_to_renewal: number;
  renewal_status: RenewalStatus;
};

export type InsuranceSummary = {
  active_count: number;
  renewals_soon: Policy[];
  overdue_renewals: Policy[];
  uninsured_assets: { asset_id: string; name: string; kind: string; value: string }[];
  monthly_cost: string;
};
