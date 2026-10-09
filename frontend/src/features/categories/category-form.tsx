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
  NO_GROUP,
  createCategorySchema,
  dreGroupOptions,
  type CreateCategoryFormValues,
} from "@/features/categories/schemas";

export function CategoryForm({
  onCreate,
}: {
  onCreate: (values: CreateCategoryFormValues) => Promise<void>;
}) {
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateCategoryFormValues>({
    resolver: zodResolver(createCategorySchema),
    defaultValues: { name: "", dre_group: NO_GROUP },
  });

  async function onSubmit(values: CreateCategoryFormValues) {
    await onCreate(values);
    reset();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-2">
        <Label htmlFor="name">Nome da categoria</Label>
        <Input id="name" placeholder="Ex: Mercado" {...register("name")} />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label>Grupo no DRE</Label>
        <Controller
          control={control}
          name="dre_group"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange} items={dreGroupOptions}>
              <SelectTrigger className="w-52">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {dreGroupOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Adicionando..." : "Adicionar categoria"}
      </Button>
    </form>
  );
}
