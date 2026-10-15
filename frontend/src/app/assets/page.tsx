"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { createAsset, listAssets } from "@/features/assets/api";
import { AssetForm } from "@/features/assets/asset-form";
import { AssetPanel } from "@/features/assets/asset-panel";
import type { Asset, AssetFormValues } from "@/features/assets/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { listDebts } from "@/features/debts/api";
import type { Debt } from "@/features/debts/schemas";

export default function AssetsPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [assets, setAssets] = useState<Asset[] | null>(null);
  const [debts, setDebts] = useState<Debt[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    Promise.all([listAssets(), listDebts()])
      .then(([assetsData, debtsData]) => {
        if (cancelled) return;
        setAssets(assetsData);
        setDebts(debtsData);
      })
      .catch(() => {
        if (!cancelled) setError("nao foi possivel carregar os bens");
      });
    return () => {
      cancelled = true;
    };
  }, [user, reloadKey]);

  async function handleCreate(values: AssetFormValues) {
    await createAsset(values);
    setShowForm(false);
    setReloadKey((key) => key + 1);
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  const linked = new Set((assets ?? []).map((asset) => asset.debt_id).filter(Boolean));
  const freeDebts = debts.filter((debt) => !linked.has(debt.id)).map((debt) => ({ id: debt.id, name: debt.name }));
  const debtNames = new Map(debts.map((debt) => [debt.id, debt.name]));

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
          <h1 className="text-2xl font-semibold">Bens</h1>
          <p className="text-muted-foreground text-sm">
            Imóveis, veículos e outros bens entram no patrimônio pelo valor estimado que você informa. Atualize a
            avaliação de tempos em tempos.
          </p>
        </div>
        {!showForm && <Button onClick={() => setShowForm(true)}>Novo bem</Button>}
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {showForm && <AssetForm debts={freeDebts} onSubmit={handleCreate} onCancel={() => setShowForm(false)} />}

      {assets === null ? (
        <p className="text-muted-foreground text-sm">Carregando...</p>
      ) : assets.length === 0 ? (
        <p className="text-muted-foreground text-sm">Nenhum bem cadastrado ainda.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {assets.map((asset) => (
            <AssetPanel
              key={asset.id}
              asset={asset}
              debtName={asset.debt_id ? (debtNames.get(asset.debt_id) ?? null) : null}
              onChanged={() => setReloadKey((key) => key + 1)}
            />
          ))}
        </div>
      )}
    </main>
  );
}
