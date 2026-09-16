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
import { accountTypeOptions, createAccountSchema, type CreateAccountFormValues } from "@/features/accounts/schemas";

export function AccountForm({ onCreate }: { onCreate: (values: CreateAccountFormValues) => Promise<void> }) {
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateAccountFormValues>({
    resolver: zodResolver(createAccountSchema),
    defaultValues: { name: "", type: "checking" },
  });

  async function onSubmit(values: CreateAccountFormValues) {
    await onCreate(values);
    reset();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-2">
        <Label htmlFor="name">Nome da conta</Label>
        <Input id="name" placeholder="Ex: Nubank" {...register("name")} />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label>Tipo</Label>
        <Controller
          control={control}
          name="type"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {accountTypeOptions.map((option) => (
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
        {isSubmitting ? "Adicionando..." : "Adicionar conta"}
      </Button>
    </form>
  );
}
