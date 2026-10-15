"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { accountTypeLabels, type Account } from "@/features/accounts/schemas";
import { formatCurrency } from "@/lib/format";

function typeLabel(type: Account["type"]): string {
  return accountTypeLabels[type] ?? type;
}

function OpeningBalanceEditor({
  account,
  onSave,
}: {
  account: Account;
  onSave: (id: string, value: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(account.opening_balance);
  const [error, setError] = useState<string | null>(null);

  if (!editing) {
    return (
      <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
        Editar saldo inicial
      </Button>
    );
  }

  return (
    <div className="flex flex-wrap items-end gap-2">
      <div className="flex flex-col gap-1">
        <Label htmlFor={`opening-${account.id}`}>Saldo inicial</Label>
        <Input
          id={`opening-${account.id}`}
          type="number"
          step="0.01"
          className="w-36"
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
      </div>
      <Button
        size="sm"
        onClick={async () => {
          setError(null);
          try {
            await onSave(account.id, value === "" ? "0" : value);
            setEditing(false);
          } catch (caught) {
            setError(caught instanceof Error ? caught.message : "erro ao salvar");
          }
        }}
      >
        Salvar
      </Button>
      <Button size="sm" variant="outline" onClick={() => setEditing(false)}>
        Cancelar
      </Button>
      {error && <p className="text-destructive w-full text-sm">{error}</p>}
    </div>
  );
}

export function AccountList({
  accounts,
  balances,
  onArchive,
  onUpdateOpeningBalance,
}: {
  accounts: Account[];
  /** Saldo atual por id de conta (de /reports/balances). Num cartão, negativo = dívida. */
  balances: Record<string, string>;
  onArchive: (id: string) => Promise<void>;
  onUpdateOpeningBalance: (id: string, value: string) => Promise<void>;
}) {
  if (accounts.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma conta cadastrada ainda.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {accounts.map((account) => {
        const balance = balances[account.id];
        const isCard = account.type === "credit_card" || account.type === "loan";
        const opening = Number(account.opening_balance);
        const hasNoOpening = opening === 0 && balance !== undefined && Number(balance) !== 0;

        return (
          <Card key={account.id}>
            <CardContent className="flex flex-col gap-3 py-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium">{account.name}</p>
                  <p className="text-muted-foreground text-sm">
                    {typeLabel(account.type)}
                    {account.is_archived && " · arquivada"}
                  </p>
                </div>
                <div className="text-right">
                  {balance !== undefined && (
                    <>
                      <p className="text-muted-foreground text-xs">
                        {isCard ? "Dívida atual" : account.type === "investment" ? "Custo da carteira" : "Saldo atual"}
                      </p>
                      <p className={`font-medium ${Number(balance) < 0 && !isCard ? "text-destructive" : ""}`}>
                        {formatCurrency(isCard ? Math.abs(Number(balance)) : balance)}
                      </p>
                    </>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-muted-foreground text-xs">
                  Saldo inicial {formatCurrency(account.opening_balance)}
                  {hasNoOpening && " · informe o saldo inicial para o saldo atual bater com o do banco"}
                </p>
                <div className="flex gap-2">
                  <OpeningBalanceEditor account={account} onSave={onUpdateOpeningBalance} />
                  {!account.is_archived && (
                    <Button variant="outline" size="sm" onClick={() => onArchive(account.id)}>
                      Arquivar
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
