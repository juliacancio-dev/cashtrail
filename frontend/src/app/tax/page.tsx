"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
import { useAuth } from "@/features/auth/auth-context";
import { downloadCsv } from "@/features/reports/api";
import { addStatement, deleteStatement, getDossier, getTaxYears, setDependents, taxCsvPath } from "@/features/tax/api";
import {
  kindLabel,
  statementKindOptions,
  type Dossier,
  type Modality,
  type StatementKind,
} from "@/features/tax/schemas";
import { formatCurrency, formatDate, monthLabel } from "@/lib/format";

function Money({ value }: { value: string }) {
  return <span className="whitespace-nowrap">{formatCurrency(value)}</span>;
}

function ModalityColumn({ modality, best }: { modality: Modality; best: boolean }) {
  const balance = Number(modality.balance);
  return (
    <div className={`flex flex-col gap-1 rounded-md border p-3 ${best ? "border-foreground" : ""}`}>
      <p className="font-medium capitalize">
        {modality.name}
        {best && <span className="text-muted-foreground text-xs font-normal"> · mais vantajosa</span>}
      </p>
      <p className="text-sm">Deduções <Money value={modality.deductions} /></p>
      <p className="text-sm">Base de cálculo <Money value={modality.base} /></p>
      <p className="text-sm">Imposto antes do redutor <Money value={modality.tax_before_reducer} /></p>
      <p className="text-sm">Redutor (Lei 15.270) <Money value={modality.reducer} /></p>
      <p className="text-sm font-medium">Imposto devido <Money value={modality.tax_due} /></p>
      <p className={`text-sm font-semibold ${balance > 0 ? "text-destructive" : ""}`}>
        {balance > 0 ? "A pagar " : balance < 0 ? "A restituir " : "Saldo "}
        <Money value={String(Math.abs(balance))} />
      </p>
    </div>
  );
}

export default function TaxPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [years, setYears] = useState<number[]>([]);
  const [year, setYear] = useState<number | null>(null);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [payer, setPayer] = useState("");
  const [kind, setKind] = useState<StatementKind>("salary");
  const [gross, setGross] = useState("");
  const [inss, setInss] = useState("");
  const [withheld, setWithheld] = useState("");

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    getTaxYears()
      .then((data) => {
        if (cancelled) return;
        setYears(data.years);
        setYear((current) => current ?? data.default_year);
      })
      .catch(() => {
        if (!cancelled) setError("nao foi possivel carregar os anos");
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  useEffect(() => {
    if (!user || year === null) return;
    let cancelled = false;
    getDossier(year)
      .then((data) => {
        if (cancelled) return;
        setDossier(data);
        setError(null);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "erro ao carregar o IRPF");
      });
    return () => {
      cancelled = true;
    };
  }, [user, year]);

  async function run(action: () => Promise<Dossier>) {
    setBusy(true);
    setError(null);
    try {
      setDossier(await action());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "erro");
    } finally {
      setBusy(false);
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const yearItems = years.map((value) => ({ value: String(value), label: String(value) }));
  const kindItems = statementKindOptions.map((option) => ({ value: option.value, label: option.label }));
  const hint = statementKindOptions.find((option) => option.value === kind)?.hint;
  const e = dossier?.estimate;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Imposto de renda</h1>
        <p className="text-muted-foreground text-sm">
          Organiza o que declarar e estima o imposto. Não é o programa da Receita, não transmite a declaração e não
          substitui um contador: confira tudo no programa oficial.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label>Ano-calendário</Label>
          {year !== null && (
            <Select value={String(year)} onValueChange={(next) => next && setYear(Number(next))} items={yearItems}>
              <SelectTrigger className="w-40" aria-label="Ano-calendário">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {yearItems.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
        {year !== null && (
          <Button
            variant="outline"
            onClick={() =>
              downloadCsv(taxCsvPath(year), `irpf-${year}.csv`).catch((caught) =>
                setError(caught instanceof Error ? caught.message : "erro ao exportar"),
              )
            }
          >
            Exportar CSV
          </Button>
        )}
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {dossier && e && (
        <>
          <p className="text-muted-foreground text-sm">
            {dossier.parameters.label}. Parâmetros consultados em {formatDate(dossier.parameters.consulted_at)}.
          </p>

          {dossier.warnings.map((warning) => (
            <p key={warning} className="rounded-md border border-amber-500/50 bg-amber-500/10 p-3 text-sm">
              {warning}
            </p>
          ))}
          {dossier.untagged_expense_categories > 0 && (
            <p className="rounded-md border p-3 text-sm">
              {dossier.untagged_expense_categories} categoria(s) de despesa com movimento no ano estão sem marca
              fiscal. Marque saúde, educação e previdência em{" "}
              <Link href="/categories" className="underline">
                Categorias
              </Link>
              .
            </p>
          )}

          <Card>
            <CardContent className="flex flex-col gap-3 py-4">
              <h2 className="font-medium">Informes de rendimentos</h2>
              <p className="text-muted-foreground text-xs">
                Digite do informe de rendimentos oficial (empresa e bancos). O salário que cai na conta é líquido:
                bruto, INSS e imposto retido só estão no informe.
              </p>
              {dossier.statements.length === 0 && <p className="text-muted-foreground text-sm">Nenhum informe.</p>}
              {dossier.statements.map((statement) => (
                <div key={statement.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span>
                    {kindLabel(statement.kind)} · {statement.payer_name}
                    <span className="text-muted-foreground">
                      {" "}
                      · bruto {formatCurrency(statement.gross_income)}
                      {Number(statement.social_security) > 0 && ` · INSS ${formatCurrency(statement.social_security)}`}
                      {Number(statement.withheld_tax) > 0 && ` · IRRF ${formatCurrency(statement.withheld_tax)}`}
                    </span>
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={busy}
                    onClick={() => run(() => deleteStatement(dossier.year, statement.id))}
                  >
                    Remover
                  </Button>
                </div>
              ))}

              <div className="flex flex-wrap items-end gap-3 rounded-md border p-3">
                <div className="flex flex-col gap-1">
                  <Label htmlFor="st-payer">Fonte pagadora</Label>
                  <Input id="st-payer" value={payer} onChange={(event) => setPayer(event.target.value)} className="w-44" />
                </div>
                <div className="flex flex-col gap-1">
                  <Label>Tipo</Label>
                  <Select value={kind} onValueChange={(next) => next && setKind(next as StatementKind)} items={kindItems}>
                    <SelectTrigger className="w-64" aria-label="Tipo do rendimento">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {kindItems.map((item) => (
                        <SelectItem key={item.value} value={item.value}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1">
                  <Label htmlFor="st-gross">Rendimento bruto</Label>
                  <Input id="st-gross" type="number" step="0.01" min="0" className="w-36" value={gross} onChange={(event) => setGross(event.target.value)} />
                </div>
                {(kind === "salary" || kind === "other_taxable") && (
                  <div className="flex flex-col gap-1">
                    <Label htmlFor="st-inss">INSS / previdência oficial</Label>
                    <Input id="st-inss" type="number" step="0.01" min="0" className="w-36" value={inss} onChange={(event) => setInss(event.target.value)} />
                  </div>
                )}
                <div className="flex flex-col gap-1">
                  <Label htmlFor="st-irrf">Imposto retido (IRRF)</Label>
                  <Input id="st-irrf" type="number" step="0.01" min="0" className="w-36" value={withheld} onChange={(event) => setWithheld(event.target.value)} />
                </div>
                <Button
                  size="sm"
                  disabled={busy || payer.trim() === "" || gross === ""}
                  onClick={() =>
                    run(async () => {
                      const result = await addStatement(dossier.year, {
                        payer_name: payer.trim(),
                        kind,
                        gross_income: gross,
                        social_security: inss || "0",
                        withheld_tax: withheld || "0",
                        note: null,
                      });
                      setPayer("");
                      setGross("");
                      setInss("");
                      setWithheld("");
                      return result;
                    })
                  }
                >
                  Adicionar informe
                </Button>
              </div>
              {hint && <p className="text-muted-foreground text-xs">{hint}</p>}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex flex-col gap-3 py-4">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <h2 className="font-medium">Estimativa do imposto do ano</h2>
                <div className="flex items-end gap-2">
                  <div className="flex flex-col gap-1">
                    <Label htmlFor="dependents">Dependentes</Label>
                    <Input
                      id="dependents"
                      type="number"
                      min="0"
                      max="20"
                      className="w-24"
                      defaultValue={dossier.dependents}
                      key={`${dossier.year}-${dossier.dependents}`}
                      onBlur={(event) => {
                        const next = Number(event.target.value);
                        if (Number.isInteger(next) && next >= 0 && next !== dossier.dependents) {
                          run(() => setDependents(dossier.year, next));
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
              <p className="text-sm">
                Rendimentos tributáveis <Money value={e.taxable_income} /> · INSS <Money value={e.social_security} /> ·
                IRRF já retido <Money value={e.withheld_tax} />
              </p>
              <p className="text-muted-foreground text-xs">
                Saúde (sem limite) <Money value={e.health} /> · educação <Money value={e.education_deducted} /> de{" "}
                <Money value={e.education_declared} /> (limite {formatCurrency(dossier.parameters.education_limit_per_person)}{" "}
                por pessoa) · previdência <Money value={e.pension_deducted} /> · dependentes{" "}
                <Money value={e.dependents_deduction} />
              </p>
              <div className="grid gap-3 md:grid-cols-2">
                <ModalityColumn modality={e.complete} best={e.best === "completa"} />
                <ModalityColumn modality={e.simplified} best={e.best === "simplificada"} />
              </div>
              {e.notes.map((note) => (
                <p key={note} className="text-muted-foreground text-xs">
                  {note}
                </p>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex flex-col gap-3 py-4">
              <h2 className="font-medium">Renda variável: apuração mensal</h2>
              <p className="text-muted-foreground text-xs">
                Ações: 15% sobre o ganho, isento se as vendas do mês somam até{" "}
                {formatCurrency(dossier.parameters.stock_exempt_monthly_sales)}. FIIs: 20%, sem isenção. O DARF
                (código {dossier.parameters.darf_code}) vence no último dia útil do mês seguinte (feriados não
                considerados). Esses ganhos ficam fora da base do imposto anual.
              </p>
              {dossier.variable_income.length === 0 ? (
                <p className="text-muted-foreground text-sm">Nenhuma venda de ação ou FII neste ano.</p>
              ) : (
                <div className="overflow-x-auto rounded-md border">
                  <table className="w-full min-w-[720px] text-sm">
                    <thead className="bg-muted/50 text-left">
                      <tr>
                        <th className="p-2">Mês</th>
                        <th className="p-2">Tipo</th>
                        <th className="p-2 text-right">Vendas</th>
                        <th className="p-2 text-right">Ganho</th>
                        <th className="p-2 text-right">Prejuízo usado</th>
                        <th className="p-2 text-right">Imposto</th>
                        <th className="p-2 text-right">DARF</th>
                        <th className="p-2">Vencimento</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dossier.variable_income.map((month) => (
                        <tr key={`${month.month}-${month.modality}`}>
                          <td className="p-2">{monthLabel(month.month)}</td>
                          <td className="p-2">{month.modality === "stock" ? "Ações" : "FII"}</td>
                          <td className="p-2 text-right"><Money value={month.sales} /></td>
                          <td className="p-2 text-right"><Money value={month.gain} /></td>
                          <td className="p-2 text-right"><Money value={month.loss_used} /></td>
                          <td className="p-2 text-right">
                            {month.exempt ? <span className="text-muted-foreground">isento</span> : <Money value={month.tax} />}
                          </td>
                          <td className="p-2 text-right font-medium">
                            <Money value={month.darf_amount} />
                            {Number(month.darf_carried) > 0 && (
                              <span className="text-muted-foreground block text-xs font-normal">
                                abaixo do mínimo: acumula {formatCurrency(month.darf_carried)}
                              </span>
                            )}
                          </td>
                          <td className="p-2">{Number(month.darf_amount) > 0 ? formatDate(month.due_date) : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {dossier.day_trade_flags.map((flag) => (
                <p key={flag} className="rounded-md border border-amber-500/50 bg-amber-500/10 p-2 text-xs">
                  {flag}
                </p>
              ))}
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardContent className="flex flex-col gap-1 py-4">
                <h2 className="font-medium">Bens e direitos em {formatDate(dossier.as_of)}</h2>
                <p className="text-muted-foreground mb-1 text-xs">Valores pelo custo, não pelo valor de mercado.</p>
                {dossier.assets_and_rights.length === 0 && <p className="text-muted-foreground text-sm">Nenhum item.</p>}
                {dossier.assets_and_rights.map((item, index) => (
                  <div key={`${item.group}-${item.name}-${index}`} className="text-sm">
                    <div className="flex justify-between gap-2">
                      <span>
                        {item.name} <span className="text-muted-foreground">· {item.group}</span>
                      </span>
                      <Money value={item.amount} />
                    </div>
                    {item.note && <p className="text-muted-foreground text-xs">{item.note}</p>}
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex flex-col gap-1 py-4">
                <h2 className="font-medium">Dívidas e ônus em {formatDate(dossier.as_of)}</h2>
                {dossier.debts.length === 0 && <p className="text-muted-foreground text-sm">Nenhuma.</p>}
                {dossier.debts.map((item, index) => (
                  <div key={`${item.group}-${item.name}-${index}`} className="flex justify-between gap-2 text-sm">
                    <span>
                      {item.name} <span className="text-muted-foreground">· {item.group}</span>
                    </span>
                    <Money value={item.amount} />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardContent className="flex flex-col gap-2 py-4">
              <h2 className="font-medium">Fontes e o que não foi verificado</h2>
              <ul className="text-sm">
                {dossier.parameters.sources.map((source) => (
                  <li key={source.url}>
                    <a href={source.url} target="_blank" rel="noreferrer" className="underline">
                      {source.topic}
                    </a>{" "}
                    <span className="text-muted-foreground">({source.kind})</span>
                  </li>
                ))}
              </ul>
              <p className="text-muted-foreground text-xs font-medium">Premissas não verificadas:</p>
              <ul className="text-muted-foreground list-disc pl-5 text-xs">
                {dossier.parameters.unverified.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </>
      )}
    </main>
  );
}
