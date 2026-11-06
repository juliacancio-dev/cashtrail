"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-context";
import { getCalendar } from "@/features/reports/api";
import { BalanceLine, DayDetail, MonthGrid, MoneySummary } from "@/features/reports/money-calendar";
import type { MoneyCalendar } from "@/features/reports/schemas";
import { currentMonthIso, monthName, shiftMonth } from "@/lib/format";

/** Ao abrir um mês: hoje, se o mês é o atual; senão, o dia mais apertado. */
function defaultDay(calendar: MoneyCalendar): string {
  return calendar.days.some((d) => d.day === calendar.today) ? calendar.today : calendar.tightest_day;
}

export default function CalendarPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [month, setMonth] = useState(() => currentMonthIso());
  const [calendar, setCalendar] = useState<MoneyCalendar | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    getCalendar(month)
      .then((data) => {
        if (!active) return;
        setCalendar(data);
        setSelected(defaultDay(data));
        setError(null);
      })
      .catch(() => active && setError("nao foi possivel carregar o calendario"));
    return () => {
      active = false;
    };
  }, [user, month]);

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const selectedDay = calendar?.days.find((d) => d.day === selected);
  const year = Number(month.slice(0, 4));
  const showYear = year !== new Date().getFullYear();

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 p-6">
      <h1 className="sr-only">Calendário do dinheiro</h1>
      {error && <p className="text-destructive text-sm">{error}</p>}

      {!calendar ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : (
        <>
          <MoneySummary calendar={calendar} />

          <section aria-label={`Mês de ${monthName(month)}`} className="flex flex-col gap-3">
            <BalanceLine days={calendar.days} selected={selected ?? ""} />
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-[17px] font-semibold">
                {monthName(month)}
                {showYear && ` de ${year}`}
              </h2>
              <div className="flex gap-1">
                <Button variant="ghost" className="size-11 rounded-full" aria-label="Mês anterior" onClick={() => setMonth((m) => shiftMonth(m, -1))}>
                  ‹
                </Button>
                {month !== currentMonthIso() && (
                  <Button variant="ghost" className="min-h-11 rounded-full" onClick={() => setMonth(currentMonthIso())}>
                    Hoje
                  </Button>
                )}
                <Button variant="ghost" className="size-11 rounded-full" aria-label="Próximo mês" onClick={() => setMonth((m) => shiftMonth(m, 1))}>
                  ›
                </Button>
              </div>
            </div>
            <MonthGrid days={calendar.days} selected={selected ?? ""} onSelect={setSelected} />
          </section>

          {selectedDay && <DayDetail day={selectedDay} />}
        </>
      )}
    </main>
  );
}
