"use client";

import { Controller, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { paymentFormSchema, type Invoice, type PaymentFormValues } from "@/features/credit-cards/schemas";
import { formatCurrency, todayIso } from "@/lib/format";

type Option = { id: string; name: string };

/** Paga a fatura (transferência da conta de origem para o cartão). Valor menor = pagamento parcial. */
export function PaymentForm({
  invoice,
  accounts,
  defaultAccountId,
  onSubmit,
  onCancel,
}: {
  invoice: Invoice;
  accounts: Option[];
  defaultAccountId: string | null;
  onSubmit: (values: PaymentFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentFormSchema),
    defaultValues: { amount: invoice.balance, paid_at: todayIso(), from_account_id: defaultAccountId ?? "" },
  });
  const entered = Number(useWatch({ control, name: "amount" }));
  const isPartial = entered > 0 && entered < Number(invoice.balance);

  async function submit(values: PaymentFormValues) {
    try {
      await onSubmit(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao pagar a fatura" });
    }
  }

  return (
    <form
      onSubmit={handleSubmit(submit)}
      className="flex flex-col gap-3 rounded-md border bg-muted/30 p-3"
      aria-label="Pagar fatura"
    >
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor={`pay-amount-${invoice.closing_date}`}>Valor (saldo {formatCurrency(invoice.balance)})</Label>
          <Input
            id={`pay-amount-${invoice.closing_date}`}
            type="number"
            step="0.01"
            min="0.01"
            max={invoice.balance}
            {...register("amount")}
          />
          {errors.amount && <p className="text-destructive text-sm">{errors.amount.message}</p>}
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor={`pay-date-${invoice.closing_date}`}>Data</Label>
          <Input id={`pay-date-${invoice.closing_date}`} type="date" max={todayIso()} {...register("paid_at")} />
          {errors.paid_at && <p className="text-destructive text-sm">{errors.paid_at.message}</p>}
        </div>

        <div className="flex flex-col gap-2">
          <Label>Pagar com</Label>
          <Controller
            control={control}
            name="from_account_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                items={accounts.map((a) => ({ value: a.id, label: a.name }))}
              >
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.from_account_id && <p className="text-destructive text-sm">{errors.from_account_id.message}</p>}
        </div>
      </div>

      <p className="text-muted-foreground text-sm">
        {isPartial
          ? `Pagamento parcial: ficarão ${formatCurrency(Number(invoice.balance) - entered)} em aberto nesta fatura.`
          : "Pagar a fatura move o dinheiro para o cartão e não conta como despesa de novo."}
      </p>

      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={isSubmitting}>
          {isSubmitting ? "Pagando..." : "Confirmar pagamento"}
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>

      {errors.root && <p className="text-destructive text-sm">{errors.root.message}</p>}
    </form>
  );
}
