import { z } from "zod";

export const NO_DEBT = "none";

export const assetKindOptions = [
  { value: "real_estate", label: "Imóvel" },
  { value: "vehicle", label: "Veículo" },
  { value: "other", label: "Outro" },
] as const;

export type AssetKind = (typeof assetKindOptions)[number]["value"];

export function kindLabel(kind: string): string {
  return assetKindOptions.find((option) => option.value === kind)?.label ?? kind;
}

const nonNegative = (message: string) =>
  z.string().refine((value) => value !== "" && Number.isFinite(Number(value)) && Number(value) >= 0, message);

export const assetFormSchema = z.object({
  name: z.string().min(1, "informe um nome"),
  kind: z.enum(["real_estate", "vehicle", "other"]),
  acquired_at: z.string().optional(),
  acquisition_value: z
    .string()
    .optional()
    .refine((value) => !value || (Number.isFinite(Number(value)) && Number(value) >= 0), "informe um valor"),
  current_value: nonNegative("informe o valor atual"),
  valued_at: z.string().min(1, "informe a data da avaliação"),
  debt_id: z.string(),
});

export type AssetFormValues = z.infer<typeof assetFormSchema>;

export type Valuation = {
  id: string;
  valued_at: string;
  value: string;
  note: string | null;
  created_at: string;
};

export type Asset = {
  id: string;
  name: string;
  kind: AssetKind;
  acquired_at: string | null;
  acquisition_value: string | null;
  debt_id: string | null;
  disposed_at: string | null;
  value: string;
  valued_at: string | null;
  is_stale: boolean;
};

export type AssetDetail = Asset & { valuations: Valuation[] };
