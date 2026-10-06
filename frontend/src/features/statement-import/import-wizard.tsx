"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { confirmImport, previewImport } from "@/features/statement-import/api";
import { MappingEditor, nativeSelectClass } from "@/features/statement-import/mapping-editor";
import { ReviewTable, formatDate } from "@/features/statement-import/review-table";
import type {
  ColumnMapping,
  ConfirmResult,
  PreviewResponse,
} from "@/features/statement-import/schemas";

type Option = { id: string; name: string };

export function ImportWizard({ accounts, categories }: { accounts: Option[]; categories: Option[] }) {
  const [accountId, setAccountId] = useState(accounts[0]?.id ?? "");
  const [defaultCategoryId, setDefaultCategoryId] = useState(categories[0]?.id ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [categoryByRow, setCategoryByRow] = useState<Record<number, string>>({});
  const [showMapping, setShowMapping] = useState(false);
  const [isWorking, setIsWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConfirmResult | null>(null);

  const validRows = preview?.rows.filter((row) => row.error === null) ?? [];
  const errorRows = preview?.rows.filter((row) => row.error !== null) ?? [];
  const duplicateCount = validRows.filter((row) => row.duplicate_of).length;

  function reset() {
    setFile(null);
    setPreview(null);
    setSelected(new Set());
    setCategoryByRow({});
    setShowMapping(false);
    setError(null);
    setResult(null);
  }

  async function runPreview(mapping?: ColumnMapping) {
    if (!file || !accountId || !defaultCategoryId) return;
    setIsWorking(true);
    setError(null);
    try {
      const response = await previewImport(file, accountId, mapping);
      const valid = response.rows.filter((row) => row.error === null);
      setPreview(response);
      // Possíveis duplicatas começam desmarcadas: quem decide é o usuário (RB-006).
      setSelected(new Set(valid.filter((row) => !row.duplicate_of).map((row) => row.row_number)));
      setCategoryByRow(Object.fromEntries(valid.map((row) => [row.row_number, defaultCategoryId])));
      setShowMapping(response.mapping === null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao ler o arquivo");
    } finally {
      setIsWorking(false);
    }
  }

  async function runConfirm() {
    if (!preview) return;
    setIsWorking(true);
    setError(null);
    try {
      const rows = validRows
        .filter((row) => selected.has(row.row_number))
        .map((row) => ({
          occurred_at: row.occurred_at!,
          type: row.type!,
          amount: row.amount!,
          description: row.description,
          category_id: categoryByRow[row.row_number],
        }));
      setResult(
        await confirmImport({
          account_id: accountId,
          file_name: preview.file_name,
          file_sha256: preview.file_sha256,
          rows_total: preview.rows.length,
          rows,
        }),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao importar os lançamentos");
    } finally {
      setIsWorking(false);
    }
  }

  function toggle(rowNumber: number) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(rowNumber)) next.delete(rowNumber);
      else next.add(rowNumber);
      return next;
    });
  }

  if (result) {
    return (
      <div className="flex flex-col gap-4 rounded-lg border p-4">
        <h2 className="text-lg font-medium">Importação concluída</h2>
        <ul className="text-sm">
          <li>{result.transactions_created} lançamento(s) criado(s)</li>
          <li>{result.rows_skipped} linha(s) não importada(s) (duplicatas, erros ou desmarcadas)</li>
        </ul>
        <div className="flex gap-3">
          <Link href="/transactions" className="underline">
            Ver lançamentos
          </Link>
          <button type="button" className="underline" onClick={reset}>
            Importar outro arquivo
          </button>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="flex max-w-md flex-col gap-4">
        <div className="flex flex-col gap-1">
          <Label htmlFor="import-account">Conta</Label>
          <select
            id="import-account"
            className={nativeSelectClass}
            value={accountId}
            onChange={(event) => setAccountId(event.target.value)}
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="import-category">Categoria padrão</Label>
          <select
            id="import-category"
            className={nativeSelectClass}
            value={defaultCategoryId}
            onChange={(event) => setDefaultCategoryId(event.target.value)}
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
          <p className="text-muted-foreground text-xs">
            Você pode trocar a categoria de cada linha na próxima etapa.
          </p>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="import-file">Extrato (.csv, até 2 MB)</Label>
          <input
            id="import-file"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </div>
        {error && <p className="text-destructive text-sm">{error}</p>}
        <div>
          <Button type="button" onClick={() => runPreview()} disabled={!file || isWorking}>
            {isWorking ? "Lendo..." : "Pré-visualizar"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm">
          <strong>{preview.file_name}</strong> — {preview.rows.length} linha(s) lida(s),{" "}
          {duplicateCount} com possível duplicata, {errorRows.length} com erro
        </p>
        <div className="flex gap-3 text-sm">
          <button type="button" className="underline" onClick={() => setShowMapping((value) => !value)}>
            {showMapping ? "Ocultar colunas" : "Ajustar colunas"}
          </button>
          <button type="button" className="underline" onClick={reset}>
            Trocar arquivo
          </button>
        </div>
      </div>

      {preview.previously_imported_at && (
        <p className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm">
          Este mesmo arquivo já foi importado nesta conta em{" "}
          {formatDate(preview.previously_imported_at.slice(0, 10))}. As linhas já importadas aparecem
          como possíveis duplicatas e vêm desmarcadas.
        </p>
      )}

      {showMapping && (
        <MappingEditor
          key={JSON.stringify(preview.mapping)}
          headers={preview.headers}
          initial={preview.mapping}
          isApplying={isWorking}
          onApply={(mapping) => runPreview(mapping)}
        />
      )}

      {preview.mapping === null && (
        <p className="text-muted-foreground text-sm">
          Não consegui identificar as colunas sozinho. Escolha acima quais colunas são a data e o valor.
        </p>
      )}

      {validRows.length > 0 && (
        <>
          <div className="flex flex-wrap gap-3 text-sm">
            <button
              type="button"
              className="underline"
              onClick={() => setSelected(new Set(validRows.map((row) => row.row_number)))}
            >
              Marcar todas
            </button>
            <button
              type="button"
              className="underline"
              onClick={() =>
                setSelected(new Set(validRows.filter((row) => !row.duplicate_of).map((row) => row.row_number)))
              }
            >
              Marcar só as sem duplicata
            </button>
            <button type="button" className="underline" onClick={() => setSelected(new Set())}>
              Desmarcar todas
            </button>
          </div>
          <ReviewTable
            rows={validRows}
            categories={categories}
            selected={selected}
            categoryByRow={categoryByRow}
            onToggle={toggle}
            onCategoryChange={(rowNumber, categoryId) =>
              setCategoryByRow((current) => ({ ...current, [rowNumber]: categoryId }))
            }
          />
        </>
      )}

      {errorRows.length > 0 && (
        <div className="rounded-lg border p-3 text-sm">
          <p className="mb-2 font-medium">Linhas com erro (não serão importadas)</p>
          <ul className="text-muted-foreground flex flex-col gap-1">
            {errorRows.map((row) => (
              <li key={row.row_number}>
                Linha {row.row_number}: {row.error}
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {validRows.length > 0 && (
        <div>
          <Button type="button" onClick={runConfirm} disabled={selected.size === 0 || isWorking}>
            {isWorking ? "Importando..." : `Importar ${selected.size} lançamento(s)`}
          </Button>
        </div>
      )}
    </div>
  );
}
