"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  dateFormatOptions,
  decimalSeparatorOptions,
  type ColumnMapping,
} from "@/features/statement-import/schemas";

export const nativeSelectClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

type ValueMode = "single" | "split";

function emptyMapping(headers: string[]): ColumnMapping {
  return {
    date_column: headers[0] ?? "",
    date_format: "%d/%m/%Y",
    decimal_separator: ",",
    description_column: null,
    amount_column: headers[1] ?? null,
    debit_column: null,
    credit_column: null,
    invert_sign: false,
  };
}

function ColumnSelect({
  id,
  label,
  value,
  headers,
  allowEmpty,
  onChange,
}: {
  id: string;
  label: string;
  value: string | null;
  headers: string[];
  allowEmpty?: boolean;
  onChange: (value: string | null) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        className={nativeSelectClass}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value || null)}
      >
        {allowEmpty && <option value="">(nenhuma)</option>}
        {headers.map((header, index) => (
          <option key={`${header}-${index}`} value={header}>
            {header || `(coluna ${index + 1})`}
          </option>
        ))}
      </select>
    </div>
  );
}

/** Deixa o usuário corrigir o que o parser adivinhou (ou escolher as colunas quando não deu para adivinhar). */
export function MappingEditor({
  headers,
  initial,
  isApplying,
  onApply,
}: {
  headers: string[];
  initial: ColumnMapping | null;
  isApplying: boolean;
  onApply: (mapping: ColumnMapping) => void;
}) {
  const [mapping, setMapping] = useState<ColumnMapping>(initial ?? emptyMapping(headers));
  const [mode, setMode] = useState<ValueMode>(
    initial && !initial.amount_column && (initial.debit_column || initial.credit_column) ? "split" : "single",
  );

  function update(patch: Partial<ColumnMapping>) {
    setMapping((current) => ({ ...current, ...patch }));
  }

  function apply() {
    onApply(
      mode === "single"
        ? { ...mapping, debit_column: null, credit_column: null }
        : { ...mapping, amount_column: null },
    );
  }

  const canApply =
    Boolean(mapping.date_column) &&
    (mode === "single" ? Boolean(mapping.amount_column) : Boolean(mapping.debit_column || mapping.credit_column));

  return (
    <div className="flex flex-col gap-4 rounded-lg border p-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <ColumnSelect
          id="map-date"
          label="Coluna da data"
          value={mapping.date_column}
          headers={headers}
          onChange={(value) => update({ date_column: value ?? "" })}
        />
        <ColumnSelect
          id="map-description"
          label="Coluna da descrição"
          value={mapping.description_column}
          headers={headers}
          allowEmpty
          onChange={(value) => update({ description_column: value })}
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label>Como o valor aparece no arquivo?</Label>
        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input type="radio" checked={mode === "single"} onChange={() => setMode("single")} />
            Uma coluna de valor (negativo = despesa)
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" checked={mode === "split"} onChange={() => setMode("split")} />
            Colunas separadas de débito e crédito
          </label>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {mode === "single" ? (
          <ColumnSelect
            id="map-amount"
            label="Coluna do valor"
            value={mapping.amount_column}
            headers={headers}
            onChange={(value) => update({ amount_column: value })}
          />
        ) : (
          <>
            <ColumnSelect
              id="map-debit"
              label="Coluna de débito"
              value={mapping.debit_column}
              headers={headers}
              allowEmpty
              onChange={(value) => update({ debit_column: value })}
            />
            <ColumnSelect
              id="map-credit"
              label="Coluna de crédito"
              value={mapping.credit_column}
              headers={headers}
              allowEmpty
              onChange={(value) => update({ credit_column: value })}
            />
          </>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <Label htmlFor="map-date-format">Formato da data</Label>
          <select
            id="map-date-format"
            className={nativeSelectClass}
            value={mapping.date_format}
            onChange={(event) => update({ date_format: event.target.value })}
          >
            {dateFormatOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="map-decimal">Separador decimal</Label>
          <select
            id="map-decimal"
            className={nativeSelectClass}
            value={mapping.decimal_separator}
            onChange={(event) => update({ decimal_separator: event.target.value as "," | "." })}
          >
            {decimalSeparatorOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={mapping.invert_sign}
          onChange={(event) => update({ invert_sign: event.target.checked })}
        />
        Inverter receita/despesa (o banco exporta despesas como valor positivo)
      </label>

      <div>
        <Button type="button" onClick={apply} disabled={!canApply || isApplying}>
          {isApplying ? "Aplicando..." : "Aplicar colunas"}
        </Button>
      </div>
    </div>
  );
}
