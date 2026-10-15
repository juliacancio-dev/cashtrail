"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-context";
import { getRetirement, savePlan, type Overview, type Scenario } from "@/features/retirement/api";
import { formatCurrency } from "@/lib/format";

function pct(fraction: string): string {
  return `${(Number(fraction) * 100).toFixed(1).replace(".", ",")}%`;
}

function whenLabel(months: number | null, age: string | null): string {
  if (months === null) return "não atinge";
  if (months === 0) return "já atingido";
  const years = Math.floor(months / 12);
  const rest = months % 12;
  return `${years}a ${rest}m (aos ${Number(age).toFixed(0)})`;
}

type Form = {
  current_age: string;
  target_age: string;
  monthly_income_wanted: string;
  public_benefit_monthly: string;
  real_return_pct: string;
  withdrawal_pct: string;
  monthly_contribution: string;
  include_assets: boolean;
};

function toForm(overview: Overview): Form {
  const plan = overview.plan;
  return {
    current_age: plan ? String(plan.current_age) : "",
    target_age: plan ? String(plan.target_age) : "",
    monthly_income_wanted: plan ? plan.monthly_income_wanted : "",
    public_benefit_monthly: plan ? plan.public_benefit_monthly : "0",
    real_return_pct: String(Number(plan?.real_return_annual ?? overview.defaults.real_return_annual) * 100),
    withdrawal_pct: String(Number(plan?.withdrawal_rate ?? overview.defaults.withdrawal_rate) * 100),
    monthly_contribution: plan ? plan.monthly_contribution : "0",
    include_assets: plan ? plan.include_assets : false,
  };
}

export default function RetirementPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [form, setForm] = useState<Form | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    getRetirement()
      .then((data) => {
        if (cancelled) return;
        setOverview(data);
        setForm(toForm(data));
      })
      .catch(() => {
        if (!cancelled) setError("nao foi possivel carregar o plano");
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  async function submit() {
    if (!form) return;
    setSaving(true);
    setError(null);
    try {
      const data = await savePlan({
        current_age: Number(form.current_age),
        target_age: Number(form.target_age),
        monthly_income_wanted: form.monthly_income_wanted,
        public_benefit_monthly: form.public_benefit_monthly || "0",
        real_return_annual: String(Number(form.real_return_pct) / 100),
        withdrawal_rate: String(Number(form.withdrawal_pct) / 100),
        monthly_contribution: form.monthly_contribution || "0",
        include_assets: form.include_assets,
      });
      setOverview(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro ao salvar o plano");
    } finally {
      setSaving(false);
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const set = (field: keyof Form) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm((current) => (current ? { ...current, [field]: event.target.value } : current));
  const result = overview?.result;
  const rates = Array.from(new Set(result?.scenarios.map((s) => s.withdrawal_rate) ?? []));
  const returns = Array.from(new Set(result?.scenarios.map((s) => s.real_return) ?? []));
  const cell = (rate: string, ret: string): Scenario | undefined =>
    result?.scenarios.find((s) => s.withdrawal_rate === rate && s.real_return === ret);

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Independência financeira</h1>
        <p className="text-muted-foreground text-sm">
          {overview?.disclaimer ??
            "Simulação com as premissas que você informar, em valores de hoje. Não é previsão nem recomendação."}
        </p>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {form && (
        <Card>
          <CardContent className="flex flex-col gap-3 py-4">
            <h2 className="font-medium">Premissas</h2>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1">
                <Label htmlFor="rt-age">Idade atual</Label>
                <Input id="rt-age" type="number" min="0" max="120" value={form.current_age} onChange={set("current_age")} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="rt-target-age">Idade-alvo</Label>
                <Input id="rt-target-age" type="number" min="1" max="120" value={form.target_age} onChange={set("target_age")} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="rt-income">Renda mensal desejada (hoje)</Label>
                <Input id="rt-income" type="number" step="0.01" min="0" value={form.monthly_income_wanted} onChange={set("monthly_income_wanted")} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="rt-benefit">Benefício público esperado (mensal)</Label>
                <Input id="rt-benefit" type="number" step="0.01" min="0" value={form.public_benefit_monthly} onChange={set("public_benefit_monthly")} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="rt-return">Retorno real ao ano (%)</Label>
                <Input id="rt-return" type="number" step="0.1" value={form.real_return_pct} onChange={set("real_return_pct")} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="rt-withdrawal">Taxa de retirada (%)</Label>
                <Input id="rt-withdrawal" type="number" step="0.1" min="0.1" value={form.withdrawal_pct} onChange={set("withdrawal_pct")} />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="rt-contribution">Aporte mensal</Label>
                <Input id="rt-contribution" type="number" step="0.01" min="0" value={form.monthly_contribution} onChange={set("monthly_contribution")} />
              </div>
              <label className="flex items-center gap-2 pt-6 text-sm sm:col-span-2">
                <input
                  type="checkbox"
                  checked={form.include_assets}
                  onChange={(event) => setForm((c) => (c ? { ...c, include_assets: event.target.checked } : c))}
                />
                Contar também meus bens (imóvel, veículo) no patrimônio
              </label>
            </div>
            <p className="text-muted-foreground text-xs">
              Retorno e retirada são <strong>premissas</strong>, não fatos: as fontes brasileiras divergem (3% a 6% de
              retirada). Os valores já preenchidos são um ponto de partida conservador. O INSS não é calculado: informe
              o benefício esperado, se quiser.
              {overview?.ipca_12m_pct && ` IPCA dos últimos 12 meses (Banco Central): ${overview.ipca_12m_pct.replace(".", ",")}%.`}
            </p>
            <div>
              <Button disabled={saving} onClick={submit}>
                {saving ? "Calculando..." : "Salvar e calcular"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {overview && (
        <p className="text-sm">
          Patrimônio considerado hoje: <strong>{formatCurrency(overview.counted_wealth)}</strong>{" "}
          <span className="text-muted-foreground">
            (investimentos a valor de mercado {formatCurrency(overview.invested_wealth)}
            {overview.plan?.include_assets ? ` + bens ${formatCurrency(overview.assets_wealth)}` : ""})
          </span>
        </p>
      )}

      {overview?.warnings.map((warning) => (
        <p key={warning} className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm">
          {warning}
        </p>
      ))}

      {result && (
        <>
          <Card>
            <CardContent className="grid gap-3 py-4 sm:grid-cols-4">
              <div>
                <p className="text-muted-foreground text-xs">Patrimônio-alvo</p>
                <p className="text-xl font-semibold">{formatCurrency(result.target)}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Progresso</p>
                <p className="text-xl font-semibold">{Number(result.progress_pct).toFixed(1).replace(".", ",")}%</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Chega lá em</p>
                <p className="text-xl font-semibold">{whenLabel(result.months_to_target, result.age_at_target)}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Já sustenta por mês</p>
                <p className="text-xl font-semibold">{formatCurrency(result.sustainable_income_today)}</p>
              </div>
            </CardContent>
          </Card>

          <p className="text-sm">
            {result.reaches_by_target_age
              ? "Com estas premissas você chega ao alvo até a idade escolhida."
              : `Para chegar na idade-alvo seria preciso aportar cerca de ${formatCurrency(result.required_contribution)} por mês.`}{" "}
            Falta {formatCurrency(result.gap)}.
          </p>

          <Card>
            <CardContent className="flex flex-col gap-2 py-4">
              <h2 className="font-medium">Cenários (quando atinge o alvo)</h2>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] text-sm">
                  <thead className="bg-muted/50 text-left">
                    <tr>
                      <th className="p-2">Taxa de retirada ↓ / retorno real →</th>
                      {returns.map((ret) => (
                        <th key={ret} className="p-2">
                          {pct(ret)} a.a.
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rates.map((rate) => (
                      <tr key={rate}>
                        <td className="p-2">
                          {pct(rate)} · alvo {formatCurrency(cell(rate, returns[0])?.target ?? "0")}
                        </td>
                        {returns.map((ret) => {
                          const item = cell(rate, ret);
                          return (
                            <td key={ret} className={`p-2 ${item?.is_base ? "font-semibold" : ""}`}>
                              {item ? whenLabel(item.months, item.age) : "—"}
                              {item?.is_base && <span className="text-muted-foreground text-xs"> · base</span>}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </main>
  );
}
