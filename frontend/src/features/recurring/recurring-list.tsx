"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { frequencyOptions, type Recurring } from "@/features/recurring/schemas";

type Option = { id: string; name: string };

function formatCurrency(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function frequencyLabel(frequency: Recurring["frequency"]): string {
  return frequencyOptions.find((option) => option.value === frequency)?.label ?? frequency;
}

export function RecurringList({
  items,
  accounts,
  categories,
  onDeactivate,
}: {
  items: Recurring[];
  accounts: Option[];
  categories: Option[];
  onDeactivate: (id: string) => Promise<void>;
}) {
  if (items.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma recorrência cadastrada ainda.</p>;
  }

  const accountName = (id: string) => accounts.find((a) => a.id === id)?.name ?? "-";
  const categoryName = (id: string) => categories.find((c) => c.id === id)?.name ?? "-";

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <Card key={item.id}>
          <CardContent className="flex items-center justify-between py-4">
            <div>
              <p className="font-medium">
                {item.description || categoryName(item.category_id)}
                {!item.is_active && (
                  <span className="text-muted-foreground text-sm font-normal"> · inativa</span>
                )}
              </p>
              <p className="text-muted-foreground text-sm">
                {accountName(item.account_id)} · {categoryName(item.category_id)} ·{" "}
                {frequencyLabel(item.frequency)} · {formatCurrency(item.amount)} · próxima em{" "}
                {item.next_occurrence_date}
              </p>
            </div>
            {item.is_active && (
              <Button variant="outline" size="sm" onClick={() => onDeactivate(item.id)}>
                Cancelar
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
