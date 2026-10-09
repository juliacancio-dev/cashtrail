const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function formatCurrency(value: string | number): string {
  return currency.format(Number(value));
}

/** "2026-10-08" -> "08/10/2026" sem passar por Date (evita deslocamento de fuso). */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

/** "2026-08" -> "ago/2026". */
export function monthLabel(month: string): string {
  const [year, number] = month.split("-");
  return `${MONTHS[Number(number) - 1]}/${year}`;
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function currentMonthIso(offset = 0): string {
  const now = new Date();
  const shifted = new Date(now.getFullYear(), now.getMonth() + offset, 1);
  return `${shifted.getFullYear()}-${pad(shifted.getMonth() + 1)}`;
}

export function firstDayOfCurrentMonthIso(): string {
  return `${currentMonthIso()}-01`;
}

export function lastDayOfCurrentMonthIso(): string {
  const now = new Date();
  const last = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return `${last.getFullYear()}-${pad(last.getMonth() + 1)}-${pad(last.getDate())}`;
}

export function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}
