"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { accountTypeOptions, type Account } from "@/features/accounts/schemas";

function typeLabel(type: Account["type"]): string {
  return accountTypeOptions.find((option) => option.value === type)?.label ?? type;
}

export function AccountList({
  accounts,
  onArchive,
}: {
  accounts: Account[];
  onArchive: (id: string) => Promise<void>;
}) {
  if (accounts.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma conta cadastrada ainda.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {accounts.map((account) => (
        <Card key={account.id}>
          <CardContent className="flex items-center justify-between py-4">
            <div>
              <p className="font-medium">{account.name}</p>
              <p className="text-muted-foreground text-sm">
                {typeLabel(account.type)}
                {account.is_archived && " · arquivada"}
              </p>
            </div>
            {!account.is_archived && (
              <Button variant="outline" size="sm" onClick={() => onArchive(account.id)}>
                Arquivar
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
