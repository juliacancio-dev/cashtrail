"use client";

import { formatCurrency } from "@/lib/format";

import type { CalendarDay, CalendarEvent, MoneyCalendar } from "./schemas";

// Calendário do dinheiro (doc 32): um número, uma frase, a linha fina e o mês. O detalhe
// aparece só para o dia escolhido, para a tela ficar calma.

const WEEKDAYS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];
const WEEKDAY_NAMES = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];
const MONTH_NAMES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

/** Dia da semana de uma data ISO, sem passar por fuso (0 = domingo). */
function weekday(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).getUTCDay();
}

function dayNumber(iso: string): number {
  return Number(iso.slice(8, 10));
}

export function monthName(month: string): string {
  return MONTH_NAMES[Number(month.slice(5, 7)) - 1];
}

function signedAmount(event: CalendarEvent): string {
  return `${event.direction === "in" ? "+" : "−"} ${formatCurrency(event.amount)}`;
}

export function MoneySummary({ calendar }: { calendar: MoneyCalendar }) {
  const isCurrent = calendar.today.slice(0, 7) === calendar.month;
  const tightest = `${calendar.tightest_day.slice(8, 10)}/${calendar.tightest_day.slice(5, 7)}`;
  const future = calendar.month > calendar.today.slice(0, 7);
  return (
    <section aria-label="Resumo" className="flex flex-col gap-2">
      <p className="font-mono text-4xl font-medium tracking-tight sm:text-5xl">
        {formatCurrency(isCurrent ? calendar.cash_today : calendar.closing_balance)}
      </p>
      <p className="text-muted-foreground text-base">
        {isCurrent
          ? "em caixa hoje. "
          : future
            ? `previsto para o fim de ${monthName(calendar.month)}. `
            : `em caixa no fim de ${monthName(calendar.month)}. `}
        O dia mais apertado do mês {future || isCurrent ? "é" : "foi"}{" "}
        <strong className="text-foreground font-semibold">{tightest}</strong>, com{" "}
        {formatCurrency(calendar.tightest_balance)}.
      </p>
    </section>
  );
}

/** Linha de saldo em degraus, sem eixos: realizado contínuo, previsão tracejada. */
export function BalanceLine({ days, selected }: { days: CalendarDay[]; selected: string }) {
  const values = days.map((d) => Number(d.balance));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const y = (v: number) => (36 - ((v - min) / span) * 32).toFixed(1);
  const width = days.length * 10;

  const path = (from: number, to: number) => {
    let d = "";
    for (let i = from; i <= to; i++) {
      const start = i === 0 ? y(values[0]) : y(values[i - 1]);
      d += d === "" ? `M${i * 10},${start} V${y(values[i])} H${(i + 1) * 10}` : ` V${y(values[i])} H${(i + 1) * 10}`;
    }
    return d;
  };
  const firstFuture = days.findIndex((d) => d.status === "future");
  const lastKnown = firstFuture === -1 ? days.length - 1 : firstFuture - 1;
  const selectedIndex = days.findIndex((d) => d.day === selected);

  return (
    <svg
      viewBox={`0 0 ${width} 40`}
      preserveAspectRatio="none"
      aria-hidden="true"
      className="block h-14 w-full"
    >
      {lastKnown >= 0 && (
        <path d={path(0, lastKnown)} fill="none" stroke="currentColor" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
      )}
      {firstFuture !== -1 && (
        <path
          d={path(firstFuture, days.length - 1)}
          fill="none"
          className="stroke-muted-foreground"
          strokeWidth={1.5}
          strokeDasharray="4 4"
          vectorEffect="non-scaling-stroke"
        />
      )}
      {selectedIndex !== -1 && (
        <circle cx={selectedIndex * 10 + 5} cy={y(values[selectedIndex])} r={2.2} className="fill-accent-money" />
      )}
    </svg>
  );
}

function dayLabel(day: CalendarDay): string {
  const parts = [`${dayNumber(day.day)}`, `saldo ${formatCurrency(day.balance)}`];
  if (day.status === "today") parts.push("hoje");
  if (day.status === "future") parts.push("previsão");
  if (day.is_tight) parts.push("dia apertado");
  if (day.events.length) parts.push(`${day.events.length} movimento${day.events.length > 1 ? "s" : ""}`);
  return parts.join(", ");
}

export function MonthGrid({
  days,
  selected,
  onSelect,
}: {
  days: CalendarDay[];
  selected: string;
  onSelect: (day: string) => void;
}) {
  const blanks = days.length ? weekday(days[0].day) : 0;
  return (
    <div role="group" aria-label="Dias do mês" className="grid grid-cols-7 gap-1">
      {WEEKDAYS.map((w) => (
        <span key={w} aria-hidden="true" className="text-muted-foreground pb-1.5 text-center text-[13px]">
          {w}
        </span>
      ))}
      {Array.from({ length: blanks }, (_, i) => (
        <span key={`blank-${i}`} aria-hidden="true" />
      ))}
      {days.map((d) => {
        const isSelected = d.day === selected;
        const tone = isSelected
          ? "bg-foreground text-background"
          : `${d.is_tight ? "bg-tight" : "hover:bg-muted"} ${
              d.status === "today" ? "text-accent-money" : d.status === "future" ? "text-muted-foreground" : ""
            }`;
        return (
          <button
            key={d.day}
            type="button"
            onClick={() => onSelect(d.day)}
            aria-pressed={isSelected}
            aria-label={dayLabel(d)}
            className={`flex h-14 flex-col items-center justify-center gap-1.5 rounded-xl transition-colors sm:h-[72px] ${tone}`}
          >
            <span className={`text-[17px] ${isSelected || d.status === "today" ? "font-semibold" : ""}`}>
              {dayNumber(d.day)}
            </span>
            <span
              aria-hidden="true"
              className={`size-[5px] rounded-full ${d.events.length ? (isSelected ? "bg-background" : "bg-muted-foreground") : ""}`}
            />
          </button>
        );
      })}
    </div>
  );
}

export function DayDetail({ day }: { day: CalendarDay }) {
  const [, month, date] = day.day.split("-");
  const title = `${WEEKDAY_NAMES[weekday(day.day)]}, ${Number(date)} de ${MONTH_NAMES[Number(month) - 1]}`;
  return (
    <section
      aria-label="Dia selecionado"
      aria-live="polite"
      className="border-border flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 border-t pt-5"
    >
      <div className="flex min-w-0 flex-col gap-1">
        <h2 className="text-muted-foreground text-[15px] font-normal">
          {title}
          {day.status === "future" && " · previsão com o que está agendado"}
          {day.status === "today" && " · hoje"}
        </h2>
        {day.events.length === 0 ? (
          <p className="text-muted-foreground text-[17px]">Sem movimentos.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {day.events.map((e, i) => (
              <li key={`${e.description}-${i}`} className="text-[17px]">
                {e.description}
                {e.kind === "planned" && day.status !== "future" && (
                  <span className="text-muted-foreground"> (pendente)</span>
                )}{" "}
                <span className="text-muted-foreground font-mono">{signedAmount(e)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="font-mono text-[22px]" aria-label={`Saldo no fim do dia: ${formatCurrency(day.balance)}`}>
        {formatCurrency(day.balance)}
      </p>
    </section>
  );
}
