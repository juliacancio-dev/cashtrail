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
  createTransactionSchema,
  transactionTypeOptions,
  type CreateTransactionFormValues,
} from "@/features/transactions/schemas";

type Option = { id: string; name: string };

export function TransactionForm({
  accounts,
  categories,
  onCreate,
}: {
  accounts: Option[];
  categories: Option[];
  onCreate: (values: CreateTransactionFormValues) => Promise<void>;
}) {
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateTransactionFormValues>({
    resolver: zodResolver(createTransactionSchema),
    defaultValues: {
      account_id: "",
      category_id: "",
      type: "expense",
      amount: "",
      description: "",
      occurred_at: new Date().toISOString().slice(0, 10),
    },
  });

  async function onSubmit(values: CreateTransactionFormValues) {
    await onCreate(values);
    reset({ ...values, amount: "", description: "" });
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
              <SelectTrigger className="w-40">
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
              <SelectTrigger className="w-40">
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
              <SelectTrigger className="w-32">
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
        <Label htmlFor="occurred_at">Data</Label>
        <Input id="occurred_at" type="date" {...register("occurred_at")} />
        {errors.occurred_at && <p className="text-sm text-destructive">{errors.occurred_at.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="description">Descrição</Label>
        <Input id="description" placeholder="Opcional" {...register("description")} />
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Adicionando..." : "Adicionar lançamento"}
      </Button>
    </form>
  );
}
