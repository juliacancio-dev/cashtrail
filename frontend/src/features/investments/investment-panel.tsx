"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  addOperation,
  archiveInvestment,
  getInvestment,
  setQuote,
  undoOperation,
} from "@/features/investments/api";
import {
  classLabel,
  operationLabels,
  type OperationKind,
  type Position,
  type PositionDetail,
} from "@/features/investments/schemas";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";

type Option = { id: string; name: string };

function plain(value: string): string {
  return Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 6 });
}

function pct(value: string | null): string {
  return value === null ? "—" : `${Number(value).toFixed(2).replace(".", ",")}%`;
}

const NONE = "none";

export function InvestmentPanel({
  position,
  cashAccounts,
  categories,
  onChanged,
}: {
  position: Position;
  cashAccounts: Option[];
  categories: Option[];
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<PositionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [busy, setBusy] = useState(false);

  const [kind, setKind] = useState<OperationKind>("buy");
  const [date, setDate] = useState(todayIso());
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [fees, setFees] = useState("");
  const [amount, setAmount] = useState("");
  const [cashId, setCashId] = useState(cashAccounts[0]?.id ?? NONE);
  const [categoryId, setCategoryId] = useState(NONE);
  const [manualPrice, setManualPrice] = useState("");

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    getInvestment(position.id)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar o ativo");
      });
    return () => {
      cancelled = true;
    };
  }, [open, position.id, reloadKey]);

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

  const cashItems = [{ value: NONE, label: "Selecione" }, ...cashAccounts.map((a) => ({ value: a.id, label: a.name }))];
  const categoryItems = [{ value: NONE, label: "Selecione" }, ...categories.map((c) => ({ value: c.id, label: c.name }))];
  const kindItems = (Object.keys(operationLabels) as OperationKind[]).map((value) => ({
    value,
    label: operationLabels[value],
  }));
  const needsCategory = kind === "income" || kind === "sell";
  const lastId = detail?.operations[0]?.id;

  function submitOperation() {
    run(async () => {
      await addOperation(position.id, {
        kind,
        occurred_at: date,
        quantity: kind === "income" ? undefined : quantity || "0",
        unit_price: kind === "buy" || kind === "sell" ? price || "0" : undefined,
        fees: kind === "buy" || kind === "sell" ? fees || "0" : undefined,
        amount: kind === "income" ? amount || "0" : undefined,
        cash_account_id: kind === "adjust" || cashId === NONE ? null : cashId,
        category_id: needsCategory && categoryId !== NONE ? categoryId : null,
      });
      setQuantity("");
      setPrice("");
      setFees("");
      setAmount("");
    });
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-medium">
              {position.name}
              {position.symbol && <span className="text-muted-foreground font-normal"> · {position.symbol}</span>}
              {position.is_archived && <span className="text-muted-foreground font-normal"> · arquivado</span>}
            </p>
            <p className="text-muted-foreground text-sm">
              {classLabel(position.asset_class)} · {plain(position.quantity)} un.
              {Number(position.quantity) > 0 && ` · preço médio ${formatCurrency(position.avg_cost)}`}
              {position.price !== null && position.price_date
                ? ` · cotação ${formatCurrency(position.price)} em ${formatDate(position.price_date)}`
                : " · sem cotação (valor pelo custo)"}
              {position.is_stale_quote && " · cotação antiga"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-muted-foreground text-xs">Valor de mercado</p>
            <p className="text-lg font-semibold">{formatCurrency(position.market_value)}</p>
          </div>
        </div>

        <p className="text-muted-foreground text-sm">
          Custo {formatCurrency(position.cost)} · resultado{" "}
          <span className={Number(position.unrealized) < 0 ? "text-destructive" : ""}>
            {formatCurrency(position.unrealized)} ({pct(position.unrealized_pct)})
          </span>{" "}
          · proventos {formatCurrency(position.income)} · realizado {formatCurrency(position.realized)} · retorno
          total {formatCurrency(position.total_return)} ({pct(position.total_return_pct)})
        </p>

        <div className="flex justify-end">
          <Button size="sm" variant="outline" onClick={() => setOpen((current) => !current)}>
            {open ? "Ocultar" : "Operações e valor"}
          </Button>
        </div>

        {open && error && <p className="text-destructive text-sm">{error}</p>}

        {open && detail && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-3 rounded-md border p-3">
              <p className="font-medium">Nova operação</p>
              <div className="flex flex-wrap items-end gap-3">
                <div className="flex flex-col gap-1">
                  <Label>Tipo</Label>
                  <Select value={kind} onValueChange={(next) => next && setKind(next as OperationKind)} items={kindItems}>
                    <SelectTrigger className="w-48" aria-label="Tipo da operação">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {kindItems.map((item) => (
                        <SelectItem key={item.value} value={item.value}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1">
                  <Label htmlFor={`op-date-${position.id}`}>Data</Label>
                  <Input
                    id={`op-date-${position.id}`}
                    type="date"
                    max={todayIso()}
                    value={date}
                    onChange={(event) => setDate(event.target.value)}
                  />
                </div>
                {kind !== "income" && (
                  <div className="flex flex-col gap-1">
                    <Label htmlFor={`op-qty-${position.id}`}>
                      {kind === "adjust" ? "Quantidade (+/−)" : "Quantidade"}
                    </Label>
                    <Input
                      id={`op-qty-${position.id}`}
                      type="number"
                      step="any"
                      className="w-32"
                      value={quantity}
                      onChange={(event) => setQuantity(event.target.value)}
                    />
                  </div>
                )}
                {(kind === "buy" || kind === "sell") && (
                  <>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`op-price-${position.id}`}>Preço unitário</Label>
                      <Input
                        id={`op-price-${position.id}`}
                        type="number"
                        step="any"
                        min="0"
                        className="w-32"
                        value={price}
                        onChange={(event) => setPrice(event.target.value)}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`op-fees-${position.id}`}>Taxas</Label>
                      <Input
                        id={`op-fees-${position.id}`}
                        type="number"
                        step="0.01"
                        min="0"
                        className="w-28"
                        value={fees}
                        onChange={(event) => setFees(event.target.value)}
                      />
                    </div>
                  </>
                )}
                {kind === "income" && (
                  <div className="flex flex-col gap-1">
                    <Label htmlFor={`op-amount-${position.id}`}>Valor recebido</Label>
                    <Input
                      id={`op-amount-${position.id}`}
                      type="number"
                      step="0.01"
                      min="0"
                      className="w-36"
                      value={amount}
                      onChange={(event) => setAmount(event.target.value)}
                    />
                  </div>
                )}
                {kind !== "adjust" && (
                  <div className="flex flex-col gap-1">
                    <Label>{kind === "buy" ? "Pagar com" : "Receber em"}</Label>
                    <Select value={cashId} onValueChange={(next) => setCashId(next ?? NONE)} items={cashItems}>
                      <SelectTrigger className="w-44" aria-label="Conta de caixa da operação">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {cashItems.map((item) => (
                          <SelectItem key={item.value} value={item.value}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
                {needsCategory && (
                  <div className="flex flex-col gap-1">
                    <Label>{kind === "income" ? "Categoria do provento" : "Categoria do ganho/perda"}</Label>
                    <Select
                      value={categoryId}
                      onValueChange={(next) => setCategoryId(next ?? NONE)}
                      items={categoryItems}
                    >
                      <SelectTrigger className="w-48" aria-label="Categoria da operação">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {categoryItems.map((item) => (
                          <SelectItem key={item.value} value={item.value}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <Button size="sm" disabled={busy} onClick={submitOperation}>
                  Registrar
                </Button>
              </div>
              <p className="text-muted-foreground text-xs">
                {kind === "buy" && "O dinheiro sai da conta e vira custo da carteira; não é despesa."}
                {kind === "sell" &&
                  "O custo volta para a conta e o ganho (ou a perda) entra uma vez no resultado, na categoria escolhida."}
                {kind === "income" && "Dividendos, JCP e rendimentos entram como receita financeira."}
                {kind === "adjust" &&
                  "Para desdobramentos e bonificações: muda a quantidade sem mexer no custo nem no caixa."}
              </p>
            </div>

            <div className="flex flex-wrap items-end gap-3 rounded-md border p-3">
              <div className="flex flex-col gap-1">
                <Label htmlFor={`quote-${position.id}`}>Informar valor atual (por unidade)</Label>
                <Input
                  id={`quote-${position.id}`}
                  type="number"
                  step="any"
                  min="0"
                  className="w-44"
                  value={manualPrice}
                  onChange={(event) => setManualPrice(event.target.value)}
                />
              </div>
              <Button
                size="sm"
                variant="outline"
                disabled={busy || manualPrice === ""}
                onClick={() =>
                  run(async () => {
                    await setQuote(position.id, manualPrice, todayIso());
                    setManualPrice("");
                  })
                }
              >
                Salvar valor
              </Button>
            </div>

            <div className="flex flex-col gap-1 text-sm">
              <p className="font-medium">Histórico</p>
              {detail.operations.length === 0 && <p className="text-muted-foreground">Nenhuma operação.</p>}
              {detail.operations.map((operation) => (
                <div key={operation.id} className="flex flex-wrap items-center justify-between gap-2">
                  <span>
                    {formatDate(operation.occurred_at)} · {operationLabels[operation.kind]}
                    {operation.kind !== "income" && ` · ${plain(operation.quantity)} un.`}
                    {(operation.kind === "buy" || operation.kind === "sell") &&
                      ` × ${formatCurrency(operation.unit_price)}`}
                    {operation.kind !== "adjust" && ` · ${formatCurrency(operation.amount)}`}
                    {operation.gain !== null && Number(operation.gain) !== 0 && (
                      <span className={Number(operation.gain) < 0 ? "text-destructive" : "text-muted-foreground"}>
                        {" "}
                        · {Number(operation.gain) > 0 ? "ganho" : "perda"} {formatCurrency(Math.abs(Number(operation.gain)))}
                      </span>
                    )}
                  </span>
                  {operation.id === lastId && (
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={busy}
                      onClick={() => run(() => undoOperation(position.id, operation.id))}
                    >
                      Desfazer
                    </Button>
                  )}
                </div>
              ))}
            </div>

            <div>
              <Button
                size="sm"
                variant="outline"
                disabled={busy}
                onClick={() => run(() => archiveInvestment(position.id, !position.is_archived))}
              >
                {position.is_archived ? "Reativar ativo" : "Arquivar ativo"}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
