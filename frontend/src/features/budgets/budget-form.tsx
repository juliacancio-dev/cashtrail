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
import { createBudgetSchema, type CreateBudgetFormValues } from "@/features/budgets/schemas";

type Option = { id: string; name: string };

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

export function BudgetForm({
  categories,
  onCreate,
}: {
  categories: Option[];
  onCreate: (values: CreateBudgetFormValues) => Promise<void>;
}) {
  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<CreateBudgetFormValues>({
    resolver: zodResolver(createBudgetSchema),
    defaultValues: { category_id: "", month: currentMonth(), limit_amount: "" },
  });

  async function onSubmit(values: CreateBudgetFormValues) {
    try {
      await onCreate(values);
      reset({ ...values, limit_amount: "" });
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao criar orcamento" });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-3">
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
        <Label htmlFor="month">Mês</Label>
        <Input id="month" type="month" {...register("month")} />
        {errors.month && <p className="text-sm text-destructive">{errors.month.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="limit_amount">Limite</Label>
        <Input
          id="limit_amount"
          type="number"
          step="0.01"
          min="0.01"
          placeholder="0,00"
          {...register("limit_amount")}
        />
        {errors.limit_amount && <p className="text-sm text-destructive">{errors.limit_amount.message}</p>}
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Adicionando..." : "Adicionar orçamento"}
      </Button>

      {errors.root && <p className="text-sm text-destructive">{errors.root.message}</p>}
    </form>
  );
}
