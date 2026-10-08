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
import { settleFormSchema, type Commitment, type SettleFormValues } from "@/features/commitments/schemas";
import { formatCurrency, todayIso } from "@/lib/format";

type Option = { id: string; name: string };

/** Baixa (pagamento/recebimento): total por padrão; um valor menor vira baixa parcial. */
export function SettleForm({
  commitment,
  accounts,
  onSubmit,
  onCancel,
}: {
  commitment: Commitment;
  accounts: Option[];
  onSubmit: (values: SettleFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const payable = commitment.direction === "payable";
  const {
    control,
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SettleFormValues>({
    resolver: zodResolver(settleFormSchema),
    defaultValues: {
      amount: commitment.balance,
      paid_at: todayIso(),
      account_id: commitment.account_id ?? "",
    },
  });

  const entered = Number(useWatch({ control, name: "amount" }));
  const remaining = Number(commitment.balance) - entered;
  const isPartial = entered > 0 && entered < Number(commitment.balance);

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-3 rounded-md border bg-muted/30 p-3"
      aria-label={payable ? "Registrar pagamento" : "Registrar recebimento"}
    >
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor={`settle-amount-${commitment.id}`}>
            {payable ? "Valor pago" : "Valor recebido"} (saldo {formatCurrency(commitment.balance)})
          </Label>
          <Input
            id={`settle-amount-${commitment.id}`}
            type="number"
            step="0.01"
            min="0.01"
            max={commitment.balance}
            {...register("amount")}
          />
          {errors.amount && <p className="text-destructive text-sm">{errors.amount.message}</p>}
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor={`settle-date-${commitment.id}`}>Data</Label>
          <Input
            id={`settle-date-${commitment.id}`}
            type="date"
            max={todayIso()}
            {...register("paid_at")}
          />
          {errors.paid_at && <p className="text-destructive text-sm">{errors.paid_at.message}</p>}
        </div>

        <div className="flex flex-col gap-2">
          <Label>Conta</Label>
          <Controller
            control={control}
            name="account_id"
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
          {errors.account_id && <p className="text-destructive text-sm">{errors.account_id.message}</p>}
        </div>
      </div>

      {isPartial && (
        <p className="text-muted-foreground text-sm">
          Baixa parcial: ficará um saldo de {formatCurrency(remaining)} em aberto.
        </p>
      )}

      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={isSubmitting}>
          {isSubmitting ? "Registrando..." : payable ? "Confirmar pagamento" : "Confirmar recebimento"}
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
