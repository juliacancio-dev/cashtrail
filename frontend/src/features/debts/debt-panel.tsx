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
  amortize,
  getDebt,
  payInstallment,
  previewAmortization,
  undoInstallmentPayment,
  updateInstallment,
} from "@/features/debts/api";
import {
  NO_ACCOUNT,
  amortizationModeOptions,
  installmentStatusLabel,
  systemLabel,
  type AmortizationMode,
  type AmortizationPreview,
  type Debt,
  type DebtDetail,
  type Installment,
} from "@/features/debts/schemas";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";

type Option = { id: string; name: string };

function InstallmentRow({
  debt,
  installment,
  accounts,
  defaultAccountId,
  onChanged,
  onError,
}: {
  debt: DebtDetail;
  installment: Installment;
  accounts: Option[];
  defaultAccountId: string;
  onChanged: () => void;
  onError: (message: string | null) => void;
}) {
  const [mode, setMode] = useState<"idle" | "pay" | "edit">("idle");
  const [paidAt, setPaidAt] = useState(todayIso());
  const [accountId, setAccountId] = useState(defaultAccountId);
  const [amount, setAmount] = useState(installment.amount);
  const [dueDate, setDueDate] = useState(installment.due_date);
  const [busy, setBusy] = useState(false);
  const isOpen = ["open", "due_today", "overdue"].includes(installment.status);
  const items = [
    { value: NO_ACCOUNT, label: "Selecione" },
    ...accounts.map((account) => ({ value: account.id, label: account.name })),
  ];

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    onError(null);
    try {
      await action();
      setMode("idle");
      onChanged();
    } catch (error) {
      onError(error instanceof Error ? error.message : "erro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <tr className={installment.status === "overdue" ? "text-destructive" : ""}>
        <td className="p-2">{installment.number}</td>
        <td className="p-2">{formatDate(installment.due_date)}</td>
        <td className="p-2 text-right">{formatCurrency(installment.amount)}</td>
        <td className="p-2 text-right">{formatCurrency(installment.principal_part)}</td>
        <td className="p-2 text-right">{formatCurrency(installment.charges)}</td>
        <td className="p-2">{installmentStatusLabel[installment.status]}</td>
        <td className="p-2 text-right whitespace-nowrap">
          {isOpen && (
            <>
              <Button size="sm" variant="ghost" onClick={() => setMode(mode === "pay" ? "idle" : "pay")}>
                Pagar
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setMode(mode === "edit" ? "idle" : "edit")}>
                Editar
              </Button>
            </>
          )}
          {installment.paid && (
            <Button
              size="sm"
              variant="ghost"
              disabled={busy}
              onClick={() => run(() => undoInstallmentPayment(debt.id, installment.id))}
            >
              Desfazer
            </Button>
          )}
        </td>
      </tr>
      {mode === "pay" && (
        <tr>
          <td colSpan={7} className="bg-muted/30 p-3">
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex flex-col gap-1">
                <Label htmlFor={`pay-date-${installment.id}`}>Data</Label>
                <Input
                  id={`pay-date-${installment.id}`}
                  type="date"
                  max={todayIso()}
                  value={paidAt}
                  onChange={(event) => setPaidAt(event.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label>Pagar com</Label>
                <Select
                  value={accountId}
                  onValueChange={(next) => setAccountId(next ?? NO_ACCOUNT)}
                  items={items}
                >
                  <SelectTrigger className="w-44" aria-label={`Conta do pagamento da parcela ${installment.number}`}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {items.map((item) => (
                      <SelectItem key={item.value} value={item.value}>
                        {item.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                size="sm"
                disabled={busy}
                onClick={() => run(() => payInstallment(debt.id, installment.id, paidAt, accountId))}
              >
                Confirmar pagamento
              </Button>
            </div>
            <p className="text-muted-foreground mt-2 text-xs">
              {formatCurrency(installment.principal_part)} reduzem a dívida e{" "}
              {formatCurrency(installment.charges)} entram como despesa de juros e encargos.
            </p>
          </td>
        </tr>
      )}
      {mode === "edit" && (
        <tr>
          <td colSpan={7} className="bg-muted/30 p-3">
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex flex-col gap-1">
                <Label htmlFor={`edit-amount-${installment.id}`}>Valor da parcela</Label>
                <Input
                  id={`edit-amount-${installment.id}`}
                  type="number"
                  step="0.01"
                  min={installment.principal_part}
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor={`edit-due-${installment.id}`}>Vencimento</Label>
                <Input
                  id={`edit-due-${installment.id}`}
                  type="date"
                  value={dueDate}
                  onChange={(event) => setDueDate(event.target.value)}
                />
              </div>
              <Button
                size="sm"
                disabled={busy}
                onClick={() => run(() => updateInstallment(debt.id, installment.id, { amount, due_date: dueDate }))}
              >
                Salvar
              </Button>
            </div>
            <p className="text-muted-foreground mt-2 text-xs">
              O valor não pode ser menor que o principal ({formatCurrency(installment.principal_part)}); a diferença
              vira encargo.
            </p>
          </td>
        </tr>
      )}
    </>
  );
}

function AmortizationForm({
  debt,
  accounts,
  defaultAccountId,
  onChanged,
}: {
  debt: DebtDetail;
  accounts: Option[];
  defaultAccountId: string;
  onChanged: () => void;
}) {
  const [amount, setAmount] = useState("");
  const [mode, setMode] = useState<AmortizationMode>("reduce_term");
  const [paidAt, setPaidAt] = useState(todayIso());
  const [accountId, setAccountId] = useState(defaultAccountId);
  const [preview, setPreview] = useState<AmortizationPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const items = [
    { value: NO_ACCOUNT, label: "Selecione" },
    ...accounts.map((account) => ({ value: account.id, label: account.name })),
  ];

  async function simulate(nextMode: AmortizationMode) {
    setError(null);
    setPreview(null);
    try {
      setPreview(await previewAmortization(debt.id, amount, nextMode));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao simular");
    }
  }

  async function confirm(nextMode: AmortizationMode) {
    setBusy(true);
    setError(null);
    try {
      await amortize(debt.id, amount, nextMode, paidAt, accountId);
      setAmount("");
      setPreview(null);
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao registrar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-md border p-3">
      <p className="font-medium">Pagamento extra ou quitação</p>
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <Label htmlFor={`amort-amount-${debt.id}`}>Valor extra de principal</Label>
          <Input
            id={`amort-amount-${debt.id}`}
            type="number"
            step="0.01"
            min="0.01"
            max={debt.outstanding}
            value={amount}
            onChange={(event) => {
              setAmount(event.target.value);
              setPreview(null);
            }}
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label>Depois de pagar</Label>
          <Select
            value={mode}
            onValueChange={(next) => {
              if (next === "reduce_term" || next === "reduce_installment") {
                setMode(next);
                setPreview(null);
              }
            }}
            items={[...amortizationModeOptions]}
          >
            <SelectTrigger className="w-64" aria-label="Efeito do pagamento extra">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {amortizationModeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor={`amort-date-${debt.id}`}>Data</Label>
          <Input
            id={`amort-date-${debt.id}`}
            type="date"
            max={todayIso()}
            value={paidAt}
            onChange={(event) => setPaidAt(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label>Pagar com</Label>
          <Select value={accountId} onValueChange={(next) => setAccountId(next ?? NO_ACCOUNT)} items={items}>
            <SelectTrigger className="w-44" aria-label="Conta do pagamento extra">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {items.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" disabled={!amount} onClick={() => simulate(mode)}>
          Simular
        </Button>
        <Button size="sm" variant="outline" onClick={() => simulate("payoff")}>
          Simular quitação ({formatCurrency(debt.outstanding)})
        </Button>
      </div>

      {preview && (
        <div className="flex flex-col gap-2 text-sm">
          <p>
            Saldo devedor: {formatCurrency(preview.outstanding_before)} →{" "}
            <strong>{formatCurrency(preview.outstanding_after)}</strong>. Parcelas em aberto:{" "}
            {preview.installments_before} → <strong>{preview.installments_after}</strong>. Juros restantes:{" "}
            {formatCurrency(preview.charges_before)} → <strong>{formatCurrency(preview.charges_after)}</strong>.
          </p>
          <p className="text-muted-foreground text-xs">
            Cálculo pelo mesmo sistema e taxa da dívida; o contrato do banco manda, confira as parcelas depois.
            Parcelas que você editou à mão voltam ao valor calculado.
          </p>
          <div>
            <Button
              size="sm"
              disabled={busy}
              onClick={() => confirm(preview.outstanding_after === "0.00" ? "payoff" : mode)}
            >
              {preview.outstanding_after === "0.00" ? "Confirmar quitação" : "Confirmar pagamento extra"}
            </Button>
          </div>
        </div>
      )}
      {error && <p className="text-destructive text-sm">{error}</p>}
    </div>
  );
}

export function DebtPanel({
  debt,
  accounts,
  onChanged,
}: {
  debt: Debt;
  accounts: Option[];
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<DebtDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    getDebt(debt.id)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar a divida");
      });
    return () => {
      cancelled = true;
    };
  }, [open, debt.id, reloadKey]);

  function changed() {
    setReloadKey((key) => key + 1);
    onChanged();
  }

  const paidShare =
    Number(debt.principal) > 0 ? Math.min(100, Math.round((Number(debt.principal_paid) / Number(debt.principal)) * 100)) : 0;
  const defaultAccount = debt.payment_account_id ?? NO_ACCOUNT;

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-medium">
              {debt.name}
              {debt.is_paid_off && <span className="text-muted-foreground text-sm font-normal"> · quitada</span>}
            </p>
            <p className="text-muted-foreground text-sm">
              {debt.creditor ? `${debt.creditor} · ` : ""}
              {systemLabel(debt.system)}
              {debt.system !== "zero" && ` · ${Number(debt.monthly_rate).toString().replace(".", ",")}% a.m.`} ·{" "}
              {debt.installments_paid} paga(s), {debt.installments_open} em aberto
            </p>
          </div>
          <div className="text-right">
            <p className="text-muted-foreground text-xs">Saldo devedor</p>
            <p className="text-lg font-semibold">{formatCurrency(debt.outstanding)}</p>
          </div>
        </div>

        <div className="bg-muted h-2 overflow-hidden rounded-full" aria-label={`${paidShare}% do principal pago`}>
          <div className="bg-foreground h-full" style={{ width: `${paidShare}%` }} />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
          <p className="text-muted-foreground">
            Principal pago {formatCurrency(debt.principal_paid)} · juros pagos {formatCurrency(debt.charges_paid)} ·
            juros a pagar {formatCurrency(debt.charges_projected)}
            {debt.next_installment &&
              ` · próxima parcela ${formatCurrency(debt.next_installment.amount)} em ${formatDate(debt.next_installment.due_date)}`}
          </p>
          <Button size="sm" variant="outline" onClick={() => setOpen((value) => !value)}>
            {open ? "Ocultar parcelas" : "Ver parcelas"}
          </Button>
        </div>

        {open && error && <p className="text-destructive text-sm">{error}</p>}

        {open && detail && (
          <div className="flex flex-col gap-3">
            <div className="max-h-96 overflow-auto rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left">
                  <tr>
                    <th className="p-2">#</th>
                    <th className="p-2">Vencimento</th>
                    <th className="p-2 text-right">Parcela</th>
                    <th className="p-2 text-right">Principal</th>
                    <th className="p-2 text-right">Encargos</th>
                    <th className="p-2">Situação</th>
                    <th className="p-2" />
                  </tr>
                </thead>
                <tbody>
                  {detail.installment_list.map((installment) => (
                    <InstallmentRow
                      key={installment.id}
                      debt={detail}
                      installment={installment}
                      accounts={accounts}
                      defaultAccountId={defaultAccount}
                      onChanged={changed}
                      onError={setError}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {!detail.is_paid_off && (
              <AmortizationForm debt={detail} accounts={accounts} defaultAccountId={defaultAccount} onChanged={changed} />
            )}

            {detail.amortizations.length > 0 && (
              <div className="text-sm">
                <p className="font-medium">Pagamentos extras</p>
                <ul className="text-muted-foreground">
                  {detail.amortizations.map((item) => (
                    <li key={item.id}>
                      {formatDate(item.paid_at)} · {formatCurrency(item.amount)} ·{" "}
                      {item.mode === "payoff"
                        ? "quitação"
                        : item.mode === "reduce_term"
                          ? "reduziu o prazo"
                          : "reduziu a parcela"}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
