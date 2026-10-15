"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { addValuation, deleteValuation, getAsset, updateAsset } from "@/features/assets/api";
import { kindLabel, type Asset, type AssetDetail } from "@/features/assets/schemas";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";

export function AssetPanel({
  asset,
  debtName,
  onChanged,
}: {
  asset: Asset;
  debtName: string | null;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<AssetDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [value, setValue] = useState("");
  const [valuedAt, setValuedAt] = useState(todayIso());
  const [note, setNote] = useState("");
  const [disposedAt, setDisposedAt] = useState(todayIso());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    getAsset(asset.id)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar o bem");
      });
    return () => {
      cancelled = true;
    };
  }, [open, asset.id, reloadKey]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      setReloadKey((key) => key + 1);
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-medium">
              {asset.name}
              {asset.disposed_at && (
                <span className="text-muted-foreground text-sm font-normal">
                  {" "}
                  · baixado em {formatDate(asset.disposed_at)}
                </span>
              )}
            </p>
            <p className="text-muted-foreground text-sm">
              {kindLabel(asset.kind)}
              {debtName && ` · financiado: ${debtName}`}
              {asset.valued_at && ` · avaliado em ${formatDate(asset.valued_at)}`}
              {asset.is_stale && " · avaliação antiga, atualize"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-muted-foreground text-xs">Valor</p>
            <p className="text-lg font-semibold">{formatCurrency(asset.value)}</p>
          </div>
        </div>

        <div className="flex justify-end">
          <Button size="sm" variant="outline" onClick={() => setOpen((current) => !current)}>
            {open ? "Ocultar" : "Avaliações"}
          </Button>
        </div>

        {open && error && <p className="text-destructive text-sm">{error}</p>}

        {open && detail && (
          <div className="flex flex-col gap-3">
            <ul className="flex flex-col gap-1 text-sm">
              {detail.valuations.map((valuation) => (
                <li key={valuation.id} className="flex items-center justify-between gap-2">
                  <span>
                    {formatDate(valuation.valued_at)} · {formatCurrency(valuation.value)}
                    {valuation.note && <span className="text-muted-foreground"> · {valuation.note}</span>}
                  </span>
                  {detail.valuations.length > 1 && (
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={busy}
                      onClick={() => run(() => deleteValuation(asset.id, valuation.id))}
                    >
                      Remover
                    </Button>
                  )}
                </li>
              ))}
            </ul>

            <div className="flex flex-wrap items-end gap-3 rounded-md border p-3">
              <div className="flex flex-col gap-1">
                <Label htmlFor={`val-value-${asset.id}`}>Novo valor</Label>
                <Input
                  id={`val-value-${asset.id}`}
                  type="number"
                  step="0.01"
                  min="0"
                  value={value}
                  onChange={(event) => setValue(event.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor={`val-date-${asset.id}`}>Data</Label>
                <Input
                  id={`val-date-${asset.id}`}
                  type="date"
                  max={todayIso()}
                  value={valuedAt}
                  onChange={(event) => setValuedAt(event.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor={`val-note-${asset.id}`}>Observação</Label>
                <Input
                  id={`val-note-${asset.id}`}
                  value={note}
                  placeholder="Ex: tabela FIPE"
                  onChange={(event) => setNote(event.target.value)}
                />
              </div>
              <Button
                size="sm"
                disabled={busy || value === ""}
                onClick={() =>
                  run(async () => {
                    await addValuation(asset.id, valuedAt, value, note);
                    setValue("");
                    setNote("");
                  })
                }
              >
                Registrar avaliação
              </Button>
            </div>

            <div className="flex flex-wrap items-end gap-3">
              {asset.disposed_at ? (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => run(() => updateAsset(asset.id, { disposed_at: null }))}
                >
                  Reativar bem
                </Button>
              ) : (
                <>
                  <div className="flex flex-col gap-1">
                    <Label htmlFor={`dispose-${asset.id}`}>Vendido ou baixado em</Label>
                    <Input
                      id={`dispose-${asset.id}`}
                      type="date"
                      max={todayIso()}
                      value={disposedAt}
                      onChange={(event) => setDisposedAt(event.target.value)}
                    />
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    onClick={() => run(() => updateAsset(asset.id, { disposed_at: disposedAt }))}
                  >
                    Dar baixa no bem
                  </Button>
                </>
              )}
            </div>
            <p className="text-muted-foreground text-xs">
              A baixa zera o bem a partir da data; o histórico anterior do patrimônio continua igual. O dinheiro
              da venda entra como lançamento normal.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
