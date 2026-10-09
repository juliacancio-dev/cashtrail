"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { listAccounts } from "@/features/accounts/api";
import type { Account } from "@/features/accounts/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { listCategories } from "@/features/categories/api";
import type { Category } from "@/features/categories/schemas";
import { createCard, listCards } from "@/features/credit-cards/api";
import { CardForm } from "@/features/credit-cards/card-form";
import { CardPanel } from "@/features/credit-cards/card-panel";
import type { Card, CardFormValues } from "@/features/credit-cards/schemas";

export default function CardsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [cards, setCards] = useState<Card[] | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    Promise.all([listAccounts(), listCategories(), listCards()])
      .then(([accountsData, categoriesData, cardsData]) => {
        if (cancelled) return;
        setAccounts(accountsData);
        setCategories(categoriesData);
        setCards(cardsData);
      })
      .catch(() => {
        if (!cancelled) setError("nao foi possivel carregar os cartoes");
      });
    return () => {
      cancelled = true;
    };
  }, [user, reloadKey]);

  async function reload() {
    setReloadKey((key) => key + 1);
  }

  async function handleCreate(values: CardFormValues) {
    await createCard(values);
    setShowForm(false);
    await reload();
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const configured = new Set((cards ?? []).map((card) => card.account_id));
  const freeCardAccounts = accounts.filter((a) => a.type === "credit_card" && !a.is_archived && !configured.has(a.id));
  const paymentAccounts = accounts.filter((a) => a.type !== "credit_card" && a.type !== "loan" && !a.is_archived);

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Cartões de crédito</h1>
          <p className="text-muted-foreground text-sm">
            A compra conta como despesa na data em que foi feita. Pagar a fatura move o dinheiro para o cartão e não
            conta de novo.
          </p>
        </div>
        <Button onClick={() => setShowForm((value) => !value)} disabled={freeCardAccounts.length === 0}>
          {showForm ? "Fechar formulário" : "Configurar cartão"}
        </Button>
      </div>

      {freeCardAccounts.length === 0 && (cards?.length ?? 0) === 0 && (
        <p className="text-muted-foreground text-sm">
          Primeiro cadastre uma conta do tipo &quot;Cartão de crédito&quot; em Contas, depois configure o fechamento e o
          vencimento aqui.
        </p>
      )}

      {showForm && freeCardAccounts.length > 0 && (
        <CardForm
          cardAccounts={freeCardAccounts}
          paymentAccounts={paymentAccounts}
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      {error && <p className="text-destructive text-sm">{error}</p>}

      {cards === null ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : (
        <div className="flex flex-col gap-4">
          {cards.map((card) => (
            <CardPanel
              key={card.id}
              card={card}
              accounts={accounts}
              categories={categories}
              onCardChanged={reload}
            />
          ))}
        </div>
      )}
    </main>
  );
}
