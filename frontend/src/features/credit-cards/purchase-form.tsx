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
import { purchaseFormSchema, type PurchaseFormValues } from "@/features/credit-cards/schemas";
import { todayIso } from "@/lib/format";

type Option = { id: string; name: string };

export function PurchaseForm({
  categories,
  onSubmit,
  onCancel,
}: {
  categories: Option[];
  onSubmit: (values: PurchaseFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PurchaseFormValues>({
    resolver: zodResolver(purchaseFormSchema),
    defaultValues: { description: "", amount: "", purchase_date: todayIso(), category_id: "", installments: "1" },
  });
  const installments = Number(useWatch({ control, name: "installments" }));

  async function submit(values: PurchaseFormValues) {
    try {
      await onSubmit(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao registrar a compra" });
    }
  }

  return (
    <form
      onSubmit={handleSubmit(submit)}
      className="flex flex-wrap items-end gap-3 rounded-md border bg-muted/30 p-3"
      aria-label="Nova compra no cartão"
    >
      <div className="flex min-w-48 flex-1 flex-col gap-2">
        <Label htmlFor="purchase-description">Descrição</Label>
        <Input id="purchase-description" placeholder="Ex.: Notebook" {...register("description")} />
        {errors.description && <p className="text-destructive text-sm">{errors.description.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="purchase-amount">{installments > 1 ? "Valor total" : "Valor"}</Label>
        <Input id="purchase-amount" type="number" step="0.01" min="0.01" placeholder="0,00" {...register("amount")} />
        {errors.amount && <p className="text-destructive text-sm">{errors.amount.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="purchase-date">Data da compra</Label>
        <Input id="purchase-date" type="date" {...register("purchase_date")} />
        {errors.purchase_date && <p className="text-destructive text-sm">{errors.purchase_date.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="purchase-installments">Parcelas</Label>
        <Input id="purchase-installments" type="number" min="1" max="60" className="w-24" {...register("installments")} />
        {errors.installments && <p className="text-destructive text-sm">{errors.installments.message}</p>}
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

      {installments > 1 && (
        <p className="text-muted-foreground w-full text-sm">
          Cria {installments} despesas, uma em cada fatura seguinte. O limite do cartão considera o valor total.
        </p>
      )}

      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={isSubmitting}>
          {isSubmitting ? "Registrando..." : "Registrar compra"}
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>

      {errors.root && <p className="text-destructive w-full text-sm">{errors.root.message}</p>}
    </form>
  );
}
