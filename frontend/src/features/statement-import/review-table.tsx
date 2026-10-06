"use client";

import { nativeSelectClass } from "@/features/statement-import/mapping-editor";
import type { PreviewRow } from "@/features/statement-import/schemas";

type Option = { id: string; name: string };

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

/** "2026-09-10" -> "10/09/2026" sem passar por Date (evita deslocamento de fuso). */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

export function ReviewTable({
  rows,
  categories,
  selected,
  categoryByRow,
  onToggle,
  onCategoryChange,
}: {
  rows: PreviewRow[];
  categories: Option[];
  selected: Set<number>;
  categoryByRow: Record<number, string>;
  onToggle: (rowNumber: number) => void;
  onCategoryChange: (rowNumber: number, categoryId: string) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left">
          <tr>
            <th className="p-2" />
            <th className="p-2">Linha</th>
            <th className="p-2">Data</th>
            <th className="p-2">Descrição</th>
            <th className="p-2 text-right">Valor</th>
            <th className="p-2">Categoria</th>
            <th className="p-2">Aviso</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.row_number} className={row.duplicate_of ? "bg-amber-500/10" : undefined}>
              <td className="p-2">
                <input
                  type="checkbox"
                  aria-label={`Importar linha ${row.row_number}`}
                  checked={selected.has(row.row_number)}
                  onChange={() => onToggle(row.row_number)}
                />
              </td>
              <td className="p-2 text-muted-foreground">{row.row_number}</td>
              <td className="p-2 whitespace-nowrap">{row.occurred_at && formatDate(row.occurred_at)}</td>
              <td className="p-2">{row.description ?? "—"}</td>
              <td
                className={`p-2 text-right whitespace-nowrap ${
                  row.type === "income" ? "text-green-600" : "text-red-600"
                }`}
              >
                {row.type === "expense" ? "−" : "+"} {currency.format(Number(row.amount))}
              </td>
              <td className="p-2">
                <select
                  className={nativeSelectClass}
                  aria-label={`Categoria da linha ${row.row_number}`}
                  value={categoryByRow[row.row_number] ?? ""}
                  onChange={(event) => onCategoryChange(row.row_number, event.target.value)}
                >
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </td>
              <td className="p-2 text-xs text-amber-700 dark:text-amber-400">
                {row.duplicate_of &&
                  `Possível duplicata de ${formatDate(row.duplicate_of.occurred_at)}${
                    row.duplicate_of.description ? ` — ${row.duplicate_of.description}` : ""
                  }`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
