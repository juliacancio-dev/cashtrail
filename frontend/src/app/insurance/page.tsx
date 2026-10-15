"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { listAssets } from "@/features/assets/api";
import type { Asset } from "@/features/assets/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import {
  createPolicy,
  deactivatePolicy,
  getInsuranceSummary,
  listPolicies,
  renewPolicy,
} from "@/features/insurance/api";
import {
  NO_ASSET,
  frequencyOptions,
  kindLabel,
  policyFormSchema,
  policyKindOptions,
  type InsuranceSummary,
  type Policy,
  type PolicyFormValues,
} from "@/features/insurance/schemas";
import { formatCurrency, formatDate, todayIso } from "@/lib/format";

type Option = { id: string; name: string };

function PolicyForm({
  accounts,
  categories,
  assets,
  onSubmit,
  onCancel,
}: {
  accounts: Option[];
  categories: Option[];
  assets: Option[];
  onSubmit: (values: PolicyFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PolicyFormValues>({
    resolver: zodResolver(policyFormSchema),
    defaultValues: {
      kind: "auto",
      insurer: "",
      name: "",
      premium_amount: "",
      premium_frequency: "monthly",
      coverage_amount: "",
      renews_on: "",
      first_due_on: todayIso(),
      asset_id: NO_ASSET,
      payment_account_id: accounts[0]?.id ?? "",
      category_id: "",
    },
  });
  const frequency = useWatch({ control, name: "premium_frequency" });
  const assetItems = [{ value: NO_ASSET, label: "Nenhum" }, ...assets.map((a) => ({ value: a.id, label: a.name }))];

  async function submit(values: PolicyFormValues) {
    try {
      await onSubmit(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "erro ao cadastrar a apólice" });
    }
  }

  const pick = (items: { value: string; label: string }[], field: { value: string; onChange: (v: string) => void }, aria: string) => (
    <Select value={field.value} onValueChange={(next) => field.onChange(next ?? "")} items={items}>
      <SelectTrigger aria-label={aria}>
        <SelectValue placeholder="Selecione" />
      </SelectTrigger>
      <SelectContent>
        {items.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );

  return (
    <form onSubmit={handleSubmit(submit)} className="flex flex-col gap-4 rounded-lg border p-4" aria-label="Nova apólice">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor="pol-name">Nome</Label>
          <Input id="pol-name" placeholder="Ex: Seguro do carro" {...register("name")} />
          {errors.name && <p className="text-destructive text-sm">{errors.name.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="pol-insurer">Seguradora</Label>
          <Input id="pol-insurer" {...register("insurer")} />
          {errors.insurer && <p className="text-destructive text-sm">{errors.insurer.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label>Tipo</Label>
          <Controller control={control} name="kind" render={({ field }) => pick([...policyKindOptions], field, "Tipo da apólice")} />
        </div>
        <div className="flex flex-col gap-2">
          <Label>Periodicidade do prêmio</Label>
          <Controller
            control={control}
            name="premium_frequency"
            render={({ field }) => pick([...frequencyOptions], field, "Periodicidade do prêmio")}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="pol-premium">Prêmio ({frequency === "monthly" ? "por mês" : "por ano"})</Label>
          <Input id="pol-premium" type="number" step="0.01" min="0.01" {...register("premium_amount")} />
          {errors.premium_amount && <p className="text-destructive text-sm">{errors.premium_amount.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="pol-coverage">Cobertura (opcional)</Label>
          <Input id="pol-coverage" type="number" step="0.01" min="0" {...register("coverage_amount")} />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="pol-renews">Renovação / fim da vigência</Label>
          <Input id="pol-renews" type="date" {...register("renews_on")} />
          {errors.renews_on && <p className="text-destructive text-sm">{errors.renews_on.message}</p>}
        </div>
        {frequency === "monthly" && (
          <div className="flex flex-col gap-2">
            <Label htmlFor="pol-first">Primeira cobrança</Label>
            <Input id="pol-first" type="date" {...register("first_due_on")} />
          </div>
        )}
        <div className="flex flex-col gap-2">
          <Label>Pagar com</Label>
          <Controller
            control={control}
            name="payment_account_id"
            render={({ field }) =>
              pick(accounts.map((a) => ({ value: a.id, label: a.name })), field, "Conta do pagamento")
            }
          />
          {errors.payment_account_id && <p className="text-destructive text-sm">{errors.payment_account_id.message}</p>}
        </div>
        <div className="flex flex-col gap-2">
          <Label>Categoria da despesa</Label>
          <Controller
            control={control}
            name="category_id"
            render={({ field }) =>
              pick(categories.map((c) => ({ value: c.id, label: c.name })), field, "Categoria do prêmio")
            }
          />
          {errors.category_id && <p className="text-destructive text-sm">{errors.category_id.message}</p>}
        </div>
        <div className="flex flex-col gap-2 sm:col-span-2">
          <Label>Bem coberto (opcional)</Label>
          <Controller control={control} name="asset_id" render={({ field }) => pick(assetItems, field, "Bem coberto")} />
          <p className="text-muted-foreground text-xs">
            O prêmio entra uma vez só em contas a pagar e no fluxo de caixa. Não guardamos número de apólice nem
            documentos.
          </p>
        </div>
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Cadastrando..." : "Cadastrar apólice"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
      {errors.root && <p className="text-destructive text-sm">{errors.root.message}</p>}
    </form>
  );
}

export default function InsurancePage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [policies, setPolicies] = useState<Policy[] | null>(null);
  const [summary, setSummary] = useState<InsuranceSummary | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [newPremium, setNewPremium] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    Promise.all([listAccounts(), listCategories(), listAssets(), listPolicies(), getInsuranceSummary()])
      .then(([a, c, s, p, sum]) => {
        if (cancelled) return;
        setAccounts(a);
        setCategories(c);
        setAssets(s);
        setPolicies(p);
        setSummary(sum);
      })
      .catch(() => {
        if (!cancelled) setError("nao foi possivel carregar os seguros");
      });
    return () => {
      cancelled = true;
    };
  }, [user, reloadKey]);

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      setReloadKey((key) => key + 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro");
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const accountOptions = accounts
    .filter((account) => !account.is_archived && account.type !== "loan" && account.type !== "investment")
    .map((account) => ({ id: account.id, name: account.name }));
  const categoryOptions = categories.filter((c) => !c.is_archived).map((c) => ({ id: c.id, name: c.name }));
  const assetOptions = assets.filter((a) => !a.disposed_at).map((a) => ({ id: a.id, name: a.name }));
  const assetNames = new Map(assets.map((asset) => [asset.id, asset.name]));

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Seguros</h1>
          <p className="text-muted-foreground text-sm">
            O prêmio vira conta a pagar (anual) ou recorrência (mensal) e entra no fluxo de caixa sem lançar duas
            vezes.
          </p>
        </div>
        {!showForm && <Button onClick={() => setShowForm(true)}>Nova apólice</Button>}
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {summary && (
        <div className="flex flex-col gap-2 text-sm">
          <p className="text-muted-foreground">
            {summary.active_count} apólice(s) ativa(s) · custo mensal equivalente {formatCurrency(summary.monthly_cost)}
          </p>
          {summary.overdue_renewals.length > 0 && (
            <p className="border-destructive/40 bg-destructive/5 rounded-md border p-3">
              Renovação vencida: {summary.overdue_renewals.map((p) => p.name).join(", ")}.
            </p>
          )}
          {summary.renewals_soon.length > 0 && (
            <p className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3">
              Renova em até 30 dias: {summary.renewals_soon.map((p) => `${p.name} (${formatDate(p.renews_on)})`).join(", ")}.
            </p>
          )}
          {summary.uninsured_assets.length > 0 && (
            <p className="rounded-md border p-3">
              Bens sem apólice ativa:{" "}
              {summary.uninsured_assets.map((a) => `${a.name} (${formatCurrency(a.value)})`).join(", ")}.{" "}
              <Link href="/assets" className="underline">
                Ver bens
              </Link>
            </p>
          )}
        </div>
      )}

      {showForm && (
        <PolicyForm
          key={accountOptions.map((a) => a.id).join(",")}
          accounts={accountOptions}
          categories={categoryOptions}
          assets={assetOptions}
          onSubmit={async (values) => {
            await createPolicy(values);
            setShowForm(false);
            setReloadKey((key) => key + 1);
          }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {policies === null ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : policies.length === 0 ? (
        <p className="text-muted-foreground text-sm">Nenhuma apólice cadastrada ainda.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {policies.map((policy) => (
            <Card key={policy.id}>
              <CardContent className="flex flex-col gap-2 py-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium">
                      {policy.name}
                      {!policy.is_active && <span className="text-muted-foreground font-normal"> · encerrada</span>}
                    </p>
                    <p className="text-muted-foreground text-sm">
                      {kindLabel(policy.kind)} · {policy.insurer}
                      {policy.asset_id && assetNames.get(policy.asset_id) && ` · cobre ${assetNames.get(policy.asset_id)}`}
                      {policy.coverage_amount && ` · cobertura ${formatCurrency(policy.coverage_amount)}`}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">
                      {formatCurrency(policy.premium_amount)}
                      <span className="text-muted-foreground text-xs font-normal">
                        {" "}
                        / {policy.premium_frequency === "monthly" ? "mês" : "ano"}
                      </span>
                    </p>
                    <p
                      className={`text-xs ${
                        policy.renewal_status === "overdue"
                          ? "text-destructive"
                          : policy.renewal_status === "soon"
                            ? "text-amber-600"
                            : "text-muted-foreground"
                      }`}
                    >
                      Renova em {formatDate(policy.renews_on)}
                      {policy.is_active && ` (${policy.days_to_renewal} dias)`}
                    </p>
                  </div>
                </div>
                {policy.is_active && (
                  <div className="flex flex-wrap items-end gap-2">
                    <div className="flex flex-col gap-1">
                      <Label htmlFor={`renew-${policy.id}`}>Novo prêmio (opcional)</Label>
                      <Input
                        id={`renew-${policy.id}`}
                        type="number"
                        step="0.01"
                        min="0.01"
                        className="w-36"
                        value={newPremium[policy.id] ?? ""}
                        onChange={(event) => setNewPremium((cur) => ({ ...cur, [policy.id]: event.target.value }))}
                      />
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => run(() => renewPolicy(policy.id, newPremium[policy.id] ?? ""))}
                    >
                      Renovar por 1 ano
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => run(() => deactivatePolicy(policy.id))}>
                      Encerrar
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </main>
  );
}
