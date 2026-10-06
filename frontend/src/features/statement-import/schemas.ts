export const dateFormatOptions = [
  { value: "%d/%m/%Y", label: "dd/mm/aaaa" },
  { value: "%Y-%m-%d", label: "aaaa-mm-dd" },
  { value: "%d-%m-%Y", label: "dd-mm-aaaa" },
  { value: "%d/%m/%y", label: "dd/mm/aa" },
  { value: "%d.%m.%Y", label: "dd.mm.aaaa" },
] as const;

export const decimalSeparatorOptions = [
  { value: ",", label: "vírgula (1.234,56)" },
  { value: ".", label: "ponto (1,234.56)" },
] as const;

export type ColumnMapping = {
  date_column: string;
  date_format: string;
  decimal_separator: "," | ".";
  description_column: string | null;
  amount_column: string | null;
  debit_column: string | null;
  credit_column: string | null;
  invert_sign: boolean;
};

export type DuplicateOf = {
  id: string;
  occurred_at: string;
  amount: string;
  description: string | null;
};

export type PreviewRow = {
  row_number: number;
  occurred_at: string | null;
  type: "income" | "expense" | null;
  amount: string | null;
  description: string | null;
  error: string | null;
  duplicate_of: DuplicateOf | null;
};

export type PreviewResponse = {
  file_name: string;
  file_sha256: string;
  encoding: string;
  delimiter: string;
  headers: string[];
  mapping: ColumnMapping | null;
  rows: PreviewRow[];
  previously_imported_at: string | null;
};

export type ConfirmRow = {
  occurred_at: string;
  type: "income" | "expense";
  amount: string;
  description: string | null;
  category_id: string;
};

export type ConfirmResult = {
  id: string;
  rows_total: number;
  transactions_created: number;
  rows_skipped: number;
};
