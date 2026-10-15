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
import {
  assetClassOptions,
  assetFormSchema,
  quoteSourceOptions,
  type AssetFormValues,
} from "@/features/investments/schemas";

type Option = { id: string; name: string };

export function InvestmentForm({
  accounts,
  onSubmit,
  onCancel,
}: {
  accounts: Option[];
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
      account_id: accounts[0]?.id ?? "",
      name: "",
      symbol: "",
      asset_class: "stock",
      quote_source: "brapi",
    },
  });
  const source = useWatch({ control, name: "quote_source" });
  const accountItems = accounts.map((account) => ({ value: account.id, label: account.name }));

  async function submit(values: AssetFormValues) {
    try {
      await onSubmit(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao cadastrar o ativo" });
    }
  }

  if (accounts.length === 0) {
    return (
      <div className="rounded-lg border p-4 text-sm">
        Antes de cadastrar um ativo, crie uma conta do tipo <strong>Investimento</strong> (corretora ou banco) em
        Contas. Ela guarda o custo da carteira.
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit(submit)}
      className="flex flex-col gap-4 rounded-lg border p-4"
      aria-label="Novo ativo"
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor="inv-name">Nome</Label>
          <Input id="inv-name" placeholder="Ex: Petrobras PN, CDB Banco X" {...register("name")} />
          {errors.name && <p className="text-destructive text-sm">{errors.name.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label>Conta de investimento</Label>
          <Controller
            control={control}
            name="account_id"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => field.onChange(next ?? "")}
                items={accountItems}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione" />
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
          {errors.account_id && <p className="text-destructive text-sm">{errors.account_id.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label>Classe</Label>
          <Controller
            control={control}
            name="asset_class"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => next && field.onChange(next)}
                items={[...assetClassOptions]}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {assetClassOptions.map((option) => (
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
          <Label>Cotação</Label>
          <Controller
            control={control}
            name="quote_source"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(next) => next && field.onChange(next)}
                items={[...quoteSourceOptions]}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {quoteSourceOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="flex flex-col gap-2 sm:col-span-2">
          <Label htmlFor="inv-symbol">Símbolo {source === "brapi" ? "" : "(opcional)"}</Label>
          <Input id="inv-symbol" placeholder="Ex: PETR4, HGLG11" {...register("symbol")} />
          {errors.symbol && <p className="text-destructive text-sm">{errors.symbol.message}</p>}
          <p className="text-muted-foreground text-xs">
            Renda fixa e fundos: use cotação manual, registre a compra com quantidade 1 e o valor aplicado, e
            informe o valor atual de tempos em tempos.
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Cadastrando..." : "Cadastrar ativo"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
      {errors.root && <p className="text-destructive text-sm">{errors.root.message}</p>}
    </form>
  );
}
