"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { Transaction } from "@/features/transactions/schemas";

type Option = { id: string; name: string };

function formatAmount(amount: string, type: Transaction["type"]): string {
  const value = Number(amount).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  return type === "expense" ? `- ${value}` : `+ ${value}`;
}

export function TransactionList({
  transactions,
  accounts,
  categories,
}: {
  transactions: Transaction[];
  accounts: Option[];
  categories: Option[];
}) {
  if (transactions.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhum lançamento cadastrado ainda.</p>;
  }

  const accountName = (id: string) => accounts.find((a) => a.id === id)?.name ?? "-";
  const categoryName = (id: string) => categories.find((c) => c.id === id)?.name ?? "-";

  return (
    <div className="flex flex-col gap-3">
      {[...transactions].reverse().map((transaction) => (
        <Card key={transaction.id}>
          <CardContent className="flex items-center justify-between py-4">
            <div>
              <p className="font-medium">
                {transaction.description || categoryName(transaction.category_id)}
              </p>
              <p className="text-muted-foreground text-sm">
                {accountName(transaction.account_id)} · {categoryName(transaction.category_id)} ·{" "}
                {transaction.occurred_at}
              </p>
            </div>
            <p
              className={
                transaction.type === "expense"
                  ? "text-destructive font-medium"
                  : "font-medium text-green-600"
              }
            >
              {formatAmount(transaction.amount, transaction.type)}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
