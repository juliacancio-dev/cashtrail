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
import { contributionSchema, type ContributionFormValues } from "@/features/goals/schemas";
import { transactionTypeOptions } from "@/features/transactions/schemas";

type Option = { id: string; name: string };

export function ContributionForm({
  accounts,
  categories,
  onSubmit: onSubmitProp,
}: {
  accounts: Option[];
  categories: Option[];
  onSubmit: (values: ContributionFormValues) => Promise<void>;
}) {
  const {
    control,
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ContributionFormValues>({
    resolver: zodResolver(contributionSchema),
    defaultValues: {
      account_id: "",
      category_id: "",
      type: "expense",
      amount: "",
      occurred_at: new Date().toISOString().slice(0, 10),
    },
  });

  return (
    <form
      onSubmit={handleSubmit(onSubmitProp)}
      className="flex flex-wrap items-end gap-2 rounded-md border p-3"
    >
      <div className="flex flex-col gap-1">
        <Label className="text-xs">Conta</Label>
        <Controller
          control={control}
          name="account_id"
          render={({ field }) => (
            <Select
              value={field.value}
              onValueChange={field.onChange}
              items={accounts.map((a) => ({ value: a.id, label: a.name }))}
            >
              <SelectTrigger className="h-8 w-32 text-xs">
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
      </div>

      <div className="flex flex-col gap-1">
        <Label className="text-xs">Categoria</Label>
        <Controller
          control={control}
          name="category_id"
          render={({ field }) => (
            <Select
              value={field.value}
              onValueChange={field.onChange}
              items={categories.map((c) => ({ value: c.id, label: c.name }))}
            >
              <SelectTrigger className="h-8 w-32 text-xs">
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
      </div>

      <div className="flex flex-col gap-1">
        <Label className="text-xs">Tipo</Label>
        <Controller
          control={control}
          name="type"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange} items={transactionTypeOptions}>
              <SelectTrigger className="h-8 w-28 text-xs">
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

      <div className="flex flex-col gap-1">
        <Label className="text-xs">Valor</Label>
        <Input className="h-8 w-24 text-xs" type="number" step="0.01" min="0.01" {...register("amount")} />
      </div>

      <div className="flex flex-col gap-1">
        <Label className="text-xs">Data</Label>
        <Input className="h-8 text-xs" type="date" {...register("occurred_at")} />
      </div>

      <Button type="submit" size="sm" disabled={isSubmitting}>
        {isSubmitting ? "Enviando..." : "Contribuir"}
      </Button>

      {(errors.account_id || errors.category_id || errors.amount || errors.occurred_at) && (
        <p className="w-full text-xs text-destructive">Preencha conta, categoria, valor e data.</p>
      )}
    </form>
  );
}
