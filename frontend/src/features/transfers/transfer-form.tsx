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
import { transferFormSchema, type TransferFormValues } from "@/features/transfers/schemas";
import { todayIso } from "@/lib/format";

type Option = { id: string; name: string };

function AccountSelect({
  label,
  value,
  onChange,
  accounts,
  error,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  accounts: Option[];
  error?: string;
}) {
  return (
    <div className="flex flex-col gap-2">
      <Label>{label}</Label>
      <Select
        value={value}
        onValueChange={(next) => onChange(next ?? "")}
        items={accounts.map((a) => ({ value: a.id, label: a.name }))}
      >
        <SelectTrigger className="w-44">
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
      {error && <p className="text-destructive text-sm">{error}</p>}
    </div>
  );
}

export function TransferForm({
  accounts,
  onCreate,
}: {
  accounts: Option[];
  onCreate: (values: TransferFormValues) => Promise<void>;
}) {
  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<TransferFormValues>({
    resolver: zodResolver(transferFormSchema),
    defaultValues: { from_account_id: "", to_account_id: "", amount: "", occurred_at: todayIso(), description: "" },
  });

  async function onSubmit(values: TransferFormValues) {
    try {
      await onCreate(values);
      reset({ ...values, amount: "", description: "" });
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao criar a transferência" });
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-wrap items-end gap-3"
      aria-label="Nova transferência"
    >
      <Controller
        control={control}
        name="from_account_id"
        render={({ field }) => (
          <AccountSelect
            label="De"
            value={field.value}
            onChange={field.onChange}
            accounts={accounts}
            error={errors.from_account_id?.message}
          />
        )}
      />
      <Controller
        control={control}
        name="to_account_id"
        render={({ field }) => (
          <AccountSelect
            label="Para"
            value={field.value}
            onChange={field.onChange}
            accounts={accounts}
            error={errors.to_account_id?.message}
          />
        )}
      />

      <div className="flex flex-col gap-2">
        <Label htmlFor="amount">Valor</Label>
        <Input id="amount" type="number" step="0.01" min="0.01" placeholder="0,00" {...register("amount")} />
        {errors.amount && <p className="text-destructive text-sm">{errors.amount.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="occurred_at">Data</Label>
        <Input id="occurred_at" type="date" max={todayIso()} {...register("occurred_at")} />
        {errors.occurred_at && <p className="text-destructive text-sm">{errors.occurred_at.message}</p>}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="description">Descrição</Label>
        <Input id="description" placeholder="Opcional" {...register("description")} />
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Transferindo..." : "Transferir"}
      </Button>

      {errors.root && <p className="text-destructive w-full text-sm">{errors.root.message}</p>}
    </form>
  );
}
