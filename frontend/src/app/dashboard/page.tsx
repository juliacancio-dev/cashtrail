"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AppNav } from "@/components/app-nav";
import { useAuth } from "@/features/auth/auth-context";
import { getDashboard } from "@/features/dashboard/api";
import type { Dashboard } from "@/features/dashboard/schemas";
import { SummaryCards } from "@/features/dashboard/summary-cards";
import { CategorySpendingChart } from "@/features/dashboard/category-spending-chart";
import { BalanceEvolutionChart } from "@/features/dashboard/balance-evolution-chart";

export default function DashboardPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    getDashboard()
      .then(setDashboard)
      .catch(() => setError("nao foi possivel carregar o dashboard"));
  }, [user]);

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        {dashboard && (
          <p className="text-muted-foreground text-sm">
            {dashboard.start_date} a {dashboard.end_date}
          </p>
        )}
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {!dashboard ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : (
        <>
          <SummaryCards summary={dashboard.summary} />

          <Card>
            <CardContent className="py-4">
              <h2 className="mb-3 text-sm font-medium">Gasto por categoria</h2>
              <CategorySpendingChart data={dashboard.by_category} />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-4">
              <h2 className="mb-3 text-sm font-medium">Evolução de saldo</h2>
              <BalanceEvolutionChart data={dashboard.balance_evolution} />
            </CardContent>
          </Card>
        </>
      )}
    </main>
  );
}
