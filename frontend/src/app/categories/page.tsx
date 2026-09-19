"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { AppNav } from "@/components/app-nav";
import { useAuth } from "@/features/auth/auth-context";
import { CategoryForm } from "@/features/categories/category-form";
import { CategoryList } from "@/features/categories/category-list";
import { archiveCategory, createCategory, listCategories } from "@/features/categories/api";
import type { Category, CreateCategoryFormValues } from "@/features/categories/schemas";

export default function CategoriesPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoadingCategories, setIsLoadingCategories] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    listCategories()
      .then(setCategories)
      .catch(() => setError("nao foi possivel carregar as categorias"))
      .finally(() => setIsLoadingCategories(false));
  }, [user]);

  async function handleCreate(values: CreateCategoryFormValues) {
    setError(null);
    try {
      const category = await createCategory(values.name);
      setCategories((current) => [...current, category]);
    } catch {
      setError("nao foi possivel criar a categoria");
    }
  }

  async function handleArchive(id: string) {
    setError(null);
    try {
      const updated = await archiveCategory(id);
      setCategories((current) => current.map((c) => (c.id === id ? updated : c)));
    } catch {
      setError("nao foi possivel arquivar a categoria");
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground text-sm">Carregando...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <AppNav />
        <Button variant="outline" onClick={() => logout().then(() => router.push("/login"))}>
          Sair
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold">Categorias</h1>
        <p className="text-muted-foreground text-sm">{user.email}</p>
      </div>

      <CategoryForm onCreate={handleCreate} />

      {error && <p className="text-destructive text-sm">{error}</p>}

      {isLoadingCategories ? (
        <p className="text-muted-foreground text-sm">Carregando categorias...</p>
      ) : (
        <CategoryList categories={categories} onArchive={handleArchive} />
      )}
    </main>
  );
}
