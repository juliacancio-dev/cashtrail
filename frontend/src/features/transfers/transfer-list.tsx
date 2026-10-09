"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Transfer } from "@/features/transfers/schemas";
import { formatCurrency, formatDate } from "@/lib/format";

type Option = { id: string; name: string };

export function TransferList({
  transfers,
  accounts,
  onDelete,
}: {
  transfers: Transfer[];
  accounts: Option[];
  onDelete: (id: string) => Promise<void>;
}) {
  const [confirming, setConfirming] = useState<string | null>(null);

  if (transfers.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma transferência registrada ainda.</p>;
  }

  const name = (id: string) => accounts.find((a) => a.id === id)?.name ?? "-";

  return (
    <div className="flex flex-col gap-3">
      {[...transfers].reverse().map((transfer) => (
        <Card key={transfer.id}>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
            <div>
              <p className="font-medium">
                {name(transfer.from_account_id)} → {name(transfer.to_account_id)}
              </p>
              <p className="text-muted-foreground text-sm">
                {formatDate(transfer.occurred_at)}
                {transfer.description && ` · ${transfer.description}`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <p className="font-medium">{formatCurrency(transfer.amount)}</p>
              {confirming === transfer.id ? (
                <>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={async () => {
                      await onDelete(transfer.id);
                      setConfirming(null);
                    }}
                  >
                    Confirmar
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setConfirming(null)}>
                    Voltar
                  </Button>
                </>
              ) : (
                <Button size="sm" variant="outline" onClick={() => setConfirming(transfer.id)}>
                  Desfazer
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
