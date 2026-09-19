"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createGoalSchema, type CreateGoalFormValues } from "@/features/goals/schemas";

export function GoalForm({
  onCreate,
}: {
  onCreate: (values: CreateGoalFormValues) => Promise<void>;
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateGoalFormValues>({
    resolver: zodResolver(createGoalSchema),
    defaultValues: { name: "", target_amount: "", target_date: "" },
  });

  async function onSubmit(values: CreateGoalFormValues) {
    await onCreate(values);
    reset();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-2">
        <Label htmlFor="name">Nome da meta</Label>
        <Input id="name" placeholder="Ex: Viagem" {...register("name")} />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="target_amount">Valor alvo</Label>
        <Input
          id="target_amount"
          type="number"
          step="0.01"
          min="0.01"
          placeholder="0,00"
          {...register("target_amount")}
        />
        {errors.target_amount && (
          <p className="text-sm text-destructive">{errors.target_amount.message}</p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="target_date">Prazo (opcional)</Label>
        <Input id="target_date" type="date" {...register("target_date")} />
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Adicionando..." : "Adicionar meta"}
      </Button>
    </form>
  );
}
