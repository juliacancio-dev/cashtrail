"use client";

import { useState } from "react";
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
import { previewSchedule } from "@/features/debts/api";
import {
  NO_ACCOUNT,
  debtFormSchema,
  systemOptions,
  type DebtFormValues,
  type SchedulePreview,
} from "@/features/debts/schemas";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";

type Option = { id: string; name: string };

export function DebtForm({
  accounts,
  categories,
  onSubmit,
  onCancel,
}: {
  accounts: Option[];
  categories: Option[];
  onSubmit: (values: DebtFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const {
    control,
    register,
    handleSubmit,
    getValues,
    trigger,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<DebtFormValues>({
    resolver: zodResolver(debtFormSchema),
    defaultValues: {
      name: "",
      creditor: "",
      principal: "",
      contracted_at: todayIso(),
      installments: "12",
      first_due_date: "",
      system: "price",
      monthly_rate: "",
      interest_category_id: "",
      payment_account_id: NO_ACCOUNT,
      received_account_id: NO_ACCOUNT,
    },
  });
  const system = useWatch({ control, name: "system" });
  const [preview, setPreview] = useState<SchedulePreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const accountItems = [
    { value: NO_ACCOUNT, label: "Nenhuma" },
    ...accounts.map((account) => ({ value: account.id, label: account.name })),
  ];
  const receivedItems = [
    { value: NO_ACCOUNT, label: "Já existia (não lançar entrada)" },
    ...accounts.map((account) => ({ value: account.id, label: account.name })),
  ];

  async function simulate() {
    setPreviewError(null);
    const valid = await trigger(["principal", "installments", "first_due_date", "monthly_rate", "system"]);
    if (!valid) return;
    try {
      setPreview(await previewSchedule(getValues()));
    } catch (error) {
      setPreview(null);
      setPreviewError(error instanceof Error ? error.message : "erro ao simular");
    }
  }

  async function submit(values: DebtFormValues) {
    try {
      await onSubmit(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao cadastrar a divida" });
    }
  }

  return (
    <form
      onSubmit={handleSubmit(submit)}
      className="flex flex-col gap-4 rounded-lg border p-4"
      aria-label="Nova dívida"
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor="debt-name">Nome</Label>
          <Input id="debt-name" placeholder="Ex: Financiamento do carro" {...register("name")} />
          {errors.name && <p className="text-destructive text-sm">{errors.name.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="debt-creditor">Credor (opcional)</Label>
          <Input id="debt-creditor" placeholder="Banco, pessoa..." {...register("creditor")} />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="debt-principal">Valor tomado (principal)</Label>
          <Input id="debt-principal" type="number" step="0.01" min="0.01" {...register("principal")} />
          {errors.principal && <p className="text-destructive text-sm">{errors.principal.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="debt-contracted">Data da contratação</Label>
          <Input id="debt-contracted" type="date" {...register("contracted_at")} />
          {errors.contracted_at && <p className="text-destructive text-sm">{errors.contracted_at.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="debt-installments">Parcelas</Label>
          <Input id="debt-installments" type="number" min="1" max="360" {...register("installments")} />
          {errors.installments && <p className="text-destructive text-sm">{errors.installments.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="debt-first-due">Primeiro vencimento</Label>
          <Input id="debt-first-due" type="date" {...register("first_due_date")} />
          {errors.first_due_date && <p className="text-destructive text-sm">{errors.first_due_date.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label>Sistema</Label>
          <Controller
            control={control}
            name="system"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => next && field.onChange(next)}
                items={[...systemOptions]}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {systemOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        {system !== "zero" && (
          <div className="flex flex-col gap-2">
            <Label htmlFor="debt-rate">Taxa de juros ao mês (%)</Label>
            <Input id="debt-rate" type="number" step="0.0001" min="0" placeholder="Ex: 1.99" {...register("monthly_rate")} />
            {errors.monthly_rate && <p className="text-destructive text-sm">{errors.monthly_rate.message}</p>}
          </div>
        )}
        <div className="flex flex-col gap-2">
          <Label>Categoria dos juros e encargos</Label>
          <Controller
            control={control}
            name="interest_category_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => field.onChange(next ?? "")}
                items={categories.map((c) => ({ value: c.id, label: c.name }))}
              >
                <SelectTrigger>
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
          {errors.interest_category_id && (
            <p className="text-destructive text-sm">{errors.interest_category_id.message}</p>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <Label>Pagar as parcelas com</Label>
          <Controller
            control={control}
            name="payment_account_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => field.onChange(next ?? NO_ACCOUNT)}
                items={accountItems}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {accountItems.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="flex flex-col gap-2 sm:col-span-2">
          <Label>Conta que recebeu o dinheiro</Label>
          <Controller
            control={control}
            name="received_account_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => field.onChange(next ?? NO_ACCOUNT)}
                items={receivedItems}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {receivedItems.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          <p className="text-muted-foreground text-xs">
            Receber o empréstimo é uma transferência, não uma receita. Se a dívida é antiga, deixe em &quot;Já
            existia&quot;: ela entra só como saldo devedor.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" size="sm" onClick={simulate}>
          Simular parcelas
        </Button>
      </div>
      {previewError && <p className="text-destructive text-sm">{previewError}</p>}

      {preview && (
        <div className="flex flex-col gap-2">
          <p className="text-sm">
            Total a pagar <strong>{formatCurrency(preview.total_paid)}</strong> · juros e encargos{" "}
            <strong>{formatCurrency(preview.total_charges)}</strong>. Se a parcela do contrato for diferente (IOF,
            seguro), edite o valor depois: a diferença vira encargo.
          </p>
          <div className="max-h-64 overflow-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left">
                <tr>
                  <th className="p-2">#</th>
                  <th className="p-2">Vencimento</th>
                  <th className="p-2 text-right">Parcela</th>
                  <th className="p-2 text-right">Principal</th>
                  <th className="p-2 text-right">Juros</th>
                  <th className="p-2 text-right">Saldo</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row) => (
                  <tr key={row.number}>
                    <td className="p-2">{row.number}</td>
                    <td className="p-2">{formatDate(row.due_date)}</td>
                    <td className="p-2 text-right">{formatCurrency(row.amount)}</td>
                    <td className="p-2 text-right">{formatCurrency(row.principal)}</td>
                    <td className="p-2 text-right">{formatCurrency(row.charges)}</td>
                    <td className="p-2 text-right">{formatCurrency(row.balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Cadastrando..." : "Cadastrar dívida"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
      {errors.root && <p className="text-destructive text-sm">{errors.root.message}</p>}
    </form>
  );
}
