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
import {
  NO_ACCOUNT,
  commitmentFormSchema,
  directionOptions,
  type Commitment,
  type CommitmentFormValues,
} from "@/features/commitments/schemas";
import { todayIso } from "@/lib/format";

type Option = { id: string; name: string };

function defaults(initial?: Commitment): CommitmentFormValues {
  if (initial) {
    return {
      direction: initial.direction,
      description: initial.description,
      counterparty: initial.counterparty ?? "",
      amount: initial.amount,
      due_date: initial.due_date,
      category_id: initial.category_id,
      account_id: initial.account_id ?? NO_ACCOUNT,
      notes: initial.notes ?? "",
      installments: "1",
    };
  }
  return {
    direction: "payable",
    description: "",
    counterparty: "",
    amount: "",
    due_date: todayIso(),
    category_id: "",
    account_id: NO_ACCOUNT,
    notes: "",
    installments: "1",
  };
}

/** Cria (com parcelamento) ou edita um compromisso. Na edição, direção e parcelas ficam fixas. */
export function CommitmentForm({
  accounts,
  categories,
  initial,
  lockValues,
  onSubmit,
  onCancel,
}: {
  accounts: Option[];
  categories: Option[];
  initial?: Commitment;
  lockValues?: boolean;
  onSubmit: (values: CommitmentFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const editing = Boolean(initial);
  const {
    control,
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CommitmentFormValues>({
    resolver: zodResolver(commitmentFormSchema),
    defaultValues: defaults(initial),
  });

  const accountItems = [
    { value: NO_ACCOUNT, label: "Definir na hora de pagar" },
    ...accounts.map((a) => ({ value: a.id, label: a.name })),
  ];
  const installments = Number(useWatch({ control, name: "installments" }));

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-4 rounded-lg border p-4"
      aria-label={editing ? "Editar conta" : "Nova conta a pagar ou receber"}
    >
      <div className="flex flex-wrap gap-3">
        {!editing && (
          <div className="flex flex-col gap-2">
            <Label>Tipo</Label>
            <Controller
              control={control}
              name="direction"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} items={directionOptions}>
                  <SelectTrigger className="w-36">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {directionOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        )}

        <div className="flex min-w-48 flex-1 flex-col gap-2">
          <Label htmlFor="description">Descrição</Label>
          <Input id="description" placeholder="Ex.: Aluguel" {...register("description")} />
          {errors.description && <p className="text-destructive text-sm">{errors.description.message}</p>}
        </div>

        <div className="flex min-w-40 flex-1 flex-col gap-2">
          <Label htmlFor="counterparty">Favorecido (opcional)</Label>
          <Input id="counterparty" placeholder="Quem recebe ou paga" {...register("counterparty")} />
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor="amount">{!editing && installments > 1 ? "Valor total" : "Valor"}</Label>
          <Input
            id="amount"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0,00"
            disabled={lockValues}
            {...register("amount")}
          />
          {errors.amount && <p className="text-destructive text-sm">{errors.amount.message}</p>}
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="due_date">{!editing && installments > 1 ? "1º vencimento" : "Vencimento"}</Label>
          <Input id="due_date" type="date" disabled={lockValues} {...register("due_date")} />
          {errors.due_date && <p className="text-destructive text-sm">{errors.due_date.message}</p>}
        </div>

        {!editing && (
          <div className="flex flex-col gap-2">
            <Label htmlFor="installments">Parcelas</Label>
            <Input
              id="installments"
              type="number"
              min="1"
              max="120"
              step="1"
              className="w-24"
              {...register("installments")}
            />
            {errors.installments && <p className="text-destructive text-sm">{errors.installments.message}</p>}
          </div>
        )}

        <div className="flex flex-col gap-2">
          <Label>Categoria</Label>
          <Controller
            control={control}
            name="category_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                items={categories.map((c) => ({ value: c.id, label: c.name }))}
              >
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category.id} value={category.id}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.category_id && <p className="text-destructive text-sm">{errors.category_id.message}</p>}
        </div>

        <div className="flex flex-col gap-2">
          <Label>Conta prevista</Label>
          <Controller
            control={control}
            name="account_id"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange} items={accountItems}>
                <SelectTrigger className="w-52">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {accountItems.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      {!editing && installments > 1 && (
        <p className="text-muted-foreground text-sm">
          O valor será dividido em {installments} parcelas mensais; se sobrar centavo, ele vai na primeira.
        </p>
      )}
      {lockValues && (
        <p className="text-muted-foreground text-sm">
          Valor e vencimento não podem mudar depois de pago ou cancelado.
        </p>
      )}

      <div className="flex flex-col gap-2">
        <Label htmlFor="notes">Observação (opcional)</Label>
        <Input id="notes" {...register("notes")} />
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Salvando..." : editing ? "Salvar alterações" : installments > 1 ? "Criar parcelas" : "Criar conta"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
