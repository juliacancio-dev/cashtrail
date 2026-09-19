"use client";

import { useForm, Controller } from "react-hook-form";
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
  createRecurringSchema,
  frequencyOptions,
  type CreateRecurringFormValues,
} from "@/features/recurring/schemas";
import { transactionTypeOptions } from "@/features/transactions/schemas";

type Option = { id: string; name: string };

export function RecurringForm({
  accounts,
  categories,
  onCreate,
}: {
  accounts: Option[];
  categories: Option[];
  onCreate: (values: CreateRecurringFormValues) => Promise<void>;
}) {
  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<CreateRecurringFormValues>({
    resolver: zodResolver(createRecurringSchema),
    defaultValues: {
      account_id: "",
      category_id: "",
      type: "expense",
      amount: "",
      description: "",
      frequency: "monthly",
      next_occurrence_date: new Date().toISOString().slice(0, 10),
    },
  });

  async function onSubmit(values: CreateRecurringFormValues) {
    try {
      await onCreate(values);
      reset({ ...values, amount: "", description: "" });
    } catch (error) {
      setError("root", {
        message: error instanceof Error ? error.message : "erro ao criar recorrencia",
      });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-3">
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
              <SelectTrigger className="w-36">
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
        {errors.account_id && <p className="text-sm text-destructive">{errors.account_id.message}</p>}
      </div>

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
              <SelectTrigger className="w-36">
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
        {errors.category_id && <p className="text-sm text-destructive">{errors.category_id.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label>Tipo</Label>
        <Controller
          control={control}
          name="type"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange} items={transactionTypeOptions}>
              <SelectTrigger className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {transactionTypeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="amount">Valor</Label>
        <Input id="amount" type="number" step="0.01" min="0.01" placeholder="0,00" {...register("amount")} />
        {errors.amount && <p className="text-sm text-destructive">{errors.amount.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label>Frequência</Label>
        <Controller
          control={control}
          name="frequency"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange} items={frequencyOptions}>
              <SelectTrigger className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {frequencyOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="next_occurrence_date">Próxima ocorrência</Label>
        <Input id="next_occurrence_date" type="date" {...register("next_occurrence_date")} />
        {errors.next_occurrence_date && (
          <p className="text-sm text-destructive">{errors.next_occurrence_date.message}</p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="description">Descrição</Label>
        <Input id="description" placeholder="Opcional" {...register("description")} />
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Adicionando..." : "Adicionar recorrência"}
      </Button>

      {errors.root && <p className="w-full text-sm text-destructive">{errors.root.message}</p>}
    </form>
  );
}
