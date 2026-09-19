"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ContributionFormValues, Goal } from "@/features/goals/schemas";
import { ContributionForm } from "@/features/goals/contribution-form";

type Option = { id: string; name: string };

function formatCurrency(value: string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function GoalList({
  goals,
  accounts,
  categories,
  onDelete,
  onContribute,
}: {
  goals: Goal[];
  accounts: Option[];
  categories: Option[];
  onDelete: (id: string) => Promise<void>;
  onContribute: (goalId: string, values: ContributionFormValues) => Promise<void>;
}) {
  const [openGoalId, setOpenGoalId] = useState<string | null>(null);

  if (goals.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma meta cadastrada ainda.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {goals.map((goal) => {
        const percent = Math.min(Number(goal.percent_achieved), 100);
        const isOpen = openGoalId === goal.id;
        return (
          <Card key={goal.id}>
            <CardContent className="flex flex-col gap-3 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    {goal.name}
                    {goal.is_achieved && (
                      <span className="text-sm font-normal text-green-600"> · atingida</span>
                    )}
                  </p>
                  <p className="text-muted-foreground text-sm">
                    {formatCurrency(goal.current_amount)} de {formatCurrency(goal.target_amount)} (
                    {goal.percent_achieved}%)
                    {goal.target_date && ` · prazo ${goal.target_date}`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setOpenGoalId(isOpen ? null : goal.id)}
                  >
                    {isOpen ? "Cancelar" : "Contribuir"}
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => onDelete(goal.id)}>
                    Excluir
                  </Button>
                </div>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full bg-green-600" style={{ width: `${percent}%` }} />
              </div>
              {isOpen && (
                <ContributionForm
                  accounts={accounts}
                  categories={categories}
                  onSubmit={async (values) => {
                    await onContribute(goal.id, values);
                    setOpenGoalId(null);
                  }}
                />
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
