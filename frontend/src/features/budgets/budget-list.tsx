"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Budget } from "@/features/budgets/schemas";

function formatCurrency(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function BudgetList({
  budgets,
  onDelete,
}: {
  budgets: Budget[];
  onDelete: (id: string) => Promise<void>;
}) {
  if (budgets.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhum orçamento cadastrado ainda.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {budgets.map((budget) => {
        const percent = Math.min(Number(budget.percent_consumed), 100);
        return (
          <Card key={budget.id}>
            <CardContent className="flex flex-col gap-2 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    {budget.category_name}
                    {budget.is_exceeded && (
                      <span className="text-destructive text-sm font-normal"> · estourado</span>
                    )}
                  </p>
                  <p className="text-muted-foreground text-sm">
                    {budget.month} · {formatCurrency(budget.spent_amount)} de{" "}
                    {formatCurrency(budget.limit_amount)} ({budget.percent_consumed}%)
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => onDelete(budget.id)}>
                  Excluir
                </Button>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={budget.is_exceeded ? "h-full bg-destructive" : "h-full bg-green-600"}
                  style={{ width: `${percent}%` }}
                />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
