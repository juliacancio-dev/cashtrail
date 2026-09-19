"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Category } from "@/features/categories/schemas";

export function CategoryList({
  categories,
  onArchive,
}: {
  categories: Category[];
  onArchive: (id: string) => Promise<void>;
}) {
  if (categories.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma categoria cadastrada ainda.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {categories.map((category) => (
        <Card key={category.id}>
          <CardContent className="flex items-center justify-between py-4">
            <p className="font-medium">
              {category.name}
              {category.is_archived && (
                <span className="text-muted-foreground text-sm font-normal"> · arquivada</span>
              )}
            </p>
            {!category.is_archived && (
              <Button variant="outline" size="sm" onClick={() => onArchive(category.id)}>
                Arquivar
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
