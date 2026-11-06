"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-context";
import { getCommitmentSummary } from "@/features/commitments/api";
import type { CommitmentSummary } from "@/features/commitments/schemas";
import { getCardsSummary } from "@/features/credit-cards/api";
import type { CardsSummary } from "@/features/credit-cards/schemas";
import { getDashboard } from "@/features/dashboard/api";
import { AttentionList, CategoryBars, MonthHero, NetWorthLine, buildNotices } from "@/features/dashboard/month-summary";
import type { Dashboard } from "@/features/dashboard/schemas";
import { getDebtsSummary } from "@/features/debts/api";
import type { DebtsSummary } from "@/features/debts/schemas";
import { getInsuranceSummary } from "@/features/insurance/api";
import type { InsuranceSummary } from "@/features/insurance/schemas";
import { getNetWorthHistory } from "@/features/reports/api";
import type { NetWorthPoint } from "@/features/reports/schemas";
import { currentMonthIso, monthName, shiftMonth } from "@/lib/format";

// Resumo do mês (doc 33, decisões 1 e 2). Os avisos e o patrimônio falam de hoje, então só aparecem no mês atual.
export default function DashboardPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [month, setMonth] = useState(() => currentMonthIso());
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [commitments, setCommitments] = useState<CommitmentSummary | null>(null);
  const [cards, setCards] = useState<CardsSummary | null>(null);
  const [debts, setDebts] = useState<DebtsSummary | null>(null);
  const [insurance, setInsurance] = useState<InsuranceSummary | null>(null);
  const [netWorth, setNetWorth] = useState<NetWorthPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    getDashboard(month)
      .then((data) => {
        if (!active) return;
        setDashboard(data);
        setError(null);
      })
      .catch(() => active && setError("Não foi possível carregar o resumo do mês."));
    return () => {
      active = false;
    };
  }, [user, month]);

  // Os avisos são extras: se algum falhar, o resumo segue sem ele.
  useEffect(() => {
    if (!user) return;
    getCommitmentSummary().then(setCommitments).catch(() => setCommitments(null));
    getCardsSummary().then(setCards).catch(() => setCards(null));
    getDebtsSummary().then(setDebts).catch(() => setDebts(null));
    getInsuranceSummary().then(setInsurance).catch(() => setInsurance(null));
    getNetWorthHistory(2).then(setNetWorth).catch(() => setNetWorth([]));
  }, [user]);

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const isCurrent = month === currentMonthIso();
  const year = Number(month.slice(0, 4));
  const title = `Resumo de ${monthName(month)}${year !== new Date().getFullYear() ? ` de ${year}` : ""}`;
  const ready = dashboard && dashboard.start_date.slice(0, 7) === month;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 p-6">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <div className="flex gap-1">
          <Button variant="ghost" className="size-11 rounded-full" aria-label="Mês anterior" onClick={() => setMonth((m) => shiftMonth(m, -1))}>
            ‹
          </Button>
          {!isCurrent && (
            <Button variant="ghost" className="min-h-11 rounded-full" onClick={() => setMonth(currentMonthIso())}>
              Este mês
            </Button>
          )}
          <Button variant="ghost" className="size-11 rounded-full" aria-label="Próximo mês" onClick={() => setMonth((m) => shiftMonth(m, 1))}>
            ›
          </Button>
        </div>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {!ready ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : (
        <>
          <MonthHero summary={dashboard.summary} month={month} isCurrent={isCurrent} />
          {isCurrent && <AttentionList notices={buildNotices({ commitments, cards, debts, insurance })} />}
          <CategoryBars data={dashboard.by_category} />
          <div className="flex flex-col gap-4">
            {isCurrent && <NetWorthLine points={netWorth} />}
            <Link href="/calendar" className="text-muted-foreground hover:text-foreground w-fit text-sm underline underline-offset-4">
              Ver o saldo dia a dia no calendário
            </Link>
          </div>
        </>
      )}
    </main>
  );
}
