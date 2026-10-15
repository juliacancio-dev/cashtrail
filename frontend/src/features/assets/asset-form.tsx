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
import {
  NO_DEBT,
  assetFormSchema,
  assetKindOptions,
  type AssetFormValues,
} from "@/features/assets/schemas";
import { todayIso } from "@/lib/format";

type Option = { id: string; name: string };

export function AssetForm({
  debts,
  onSubmit,
  onCancel,
}: {
  debts: Option[];
  onSubmit: (values: AssetFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<AssetFormValues>({
    resolver: zodResolver(assetFormSchema),
    defaultValues: {
      name: "",
      kind: "vehicle",
      acquired_at: "",
      acquisition_value: "",
      current_value: "",
      valued_at: todayIso(),
      debt_id: NO_DEBT,
    },
  });
  const debtItems = [{ value: NO_DEBT, label: "Sem financiamento" }, ...debts.map((d) => ({ value: d.id, label: d.name }))];

  async function submit(values: AssetFormValues) {
    try {
      await onSubmit(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao cadastrar o bem" });
    }
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="flex flex-col gap-4 rounded-lg border p-4" aria-label="Novo bem">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor="asset-name">Nome</Label>
          <Input id="asset-name" placeholder="Ex: Apartamento, Carro" {...register("name")} />
          {errors.name && <p className="text-destructive text-sm">{errors.name.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label>Tipo</Label>
          <Controller
            control={control}
            name="kind"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => next && field.onChange(next)}
                items={[...assetKindOptions]}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {assetKindOptions.map((option) => (
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
          <Label htmlFor="asset-value">Valor atual estimado</Label>
          <Input id="asset-value" type="number" step="0.01" min="0" {...register("current_value")} />
          {errors.current_value && <p className="text-destructive text-sm">{errors.current_value.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="asset-valued-at">Data da avaliação</Label>
          <Input id="asset-valued-at" type="date" max={todayIso()} {...register("valued_at")} />
          {errors.valued_at && <p className="text-destructive text-sm">{errors.valued_at.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="asset-acquired">Data da compra (opcional)</Label>
          <Input id="asset-acquired" type="date" {...register("acquired_at")} />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="asset-acq-value">Valor pago (opcional)</Label>
          <Input id="asset-acq-value" type="number" step="0.01" min="0" {...register("acquisition_value")} />
          {errors.acquisition_value && <p className="text-destructive text-sm">{errors.acquisition_value.message}</p>}
        </div>
        <div className="flex flex-col gap-2 sm:col-span-2">
          <Label>Financiamento deste bem</Label>
          <Controller
            control={control}
            name="debt_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => field.onChange(next ?? NO_DEBT)}
                items={debtItems}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {debtItems.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          <p className="text-muted-foreground text-xs">
            Só informativo: mostra quanto do bem é seu (valor − saldo devedor). Não muda nenhum total.
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Cadastrando..." : "Cadastrar bem"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
      {errors.root && <p className="text-destructive text-sm">{errors.root.message}</p>}
    </form>
  );
}
