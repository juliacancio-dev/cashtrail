"use client";

import { Controller, useForm } from "react-hook-form";
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
import { NO_ACCOUNT, cardFormSchema, type Card, type CardFormValues } from "@/features/credit-cards/schemas";

type Option = { id: string; name: string };

/** Cria a configuração de um cartão (escolhe a conta) ou edita fechamento, vencimento, limite e conta de pagamento. */
export function CardForm({
  cardAccounts,
  paymentAccounts,
  initial,
  onSubmit,
  onCancel,
}: {
  cardAccounts: Option[];
  paymentAccounts: Option[];
  initial?: Card;
  onSubmit: (values: CardFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const editing = Boolean(initial);
  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<CardFormValues>({
    resolver: zodResolver(cardFormSchema),
    defaultValues: {
      account_id: initial?.account_id ?? cardAccounts[0]?.id ?? "",
      closing_day: String(initial?.closing_day ?? ""),
      due_day: String(initial?.due_day ?? ""),
      credit_limit: initial?.credit_limit ?? "",
      default_payment_account_id: initial?.default_payment_account_id ?? NO_ACCOUNT,
    },
  });

  const paymentItems = [
    { value: NO_ACCOUNT, label: "Escolher na hora de pagar" },
    ...paymentAccounts.map((a) => ({ value: a.id, label: a.name })),
  ];

  async function submit(values: CardFormValues) {
    try {
      await onSubmit(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao salvar o cartão" });
    }
  }

  return (
    <form
      onSubmit={handleSubmit(submit)}
      className="flex flex-wrap items-end gap-3 rounded-lg border p-4"
      aria-label={editing ? "Editar cartão" : "Configurar cartão"}
    >
      {!editing && (
        <div className="flex flex-col gap-2">
          <Label>Conta do cartão</Label>
          <Controller
            control={control}
            name="account_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                items={cardAccounts.map((a) => ({ value: a.id, label: a.name }))}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {cardAccounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      )}

      <div className="flex flex-col gap-2">
        <Label htmlFor="closing_day">Dia de fechamento</Label>
        <Input id="closing_day" type="number" min="1" max="31" className="w-32" {...register("closing_day")} />
        {errors.closing_day && <p className="text-destructive text-sm">{errors.closing_day.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="due_day">Dia de vencimento</Label>
        <Input id="due_day" type="number" min="1" max="31" className="w-32" {...register("due_day")} />
        {errors.due_day && <p className="text-destructive text-sm">{errors.due_day.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="credit_limit">Limite (opcional)</Label>
        <Input id="credit_limit" type="number" step="0.01" min="0.01" placeholder="0,00" {...register("credit_limit")} />
        {errors.credit_limit && <p className="text-destructive text-sm">{errors.credit_limit.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label>Pagar a fatura com</Label>
        <Controller
          control={control}
          name="default_payment_account_id"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange} items={paymentItems}>
              <SelectTrigger className="w-52">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {paymentItems.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <p className="text-muted-foreground w-full text-xs">
        A compra feita até o dia de fechamento, inclusive, entra na fatura que fecha. Se o seu banco fizer
        diferente, mova a compra para a fatura certa depois de lançá-la.
      </p>

      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Salvando..." : editing ? "Salvar" : "Configurar cartão"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>

      {errors.root && <p className="text-destructive w-full text-sm">{errors.root.message}</p>}
    </form>
  );
}
