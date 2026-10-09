"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { NO_GROUP, dreGroupOptions, type Category } from "@/features/categories/schemas";

export function CategoryList({
  categories,
  onArchive,
  onChangeGroup,
}: {
  categories: Category[];
  onArchive: (id: string) => Promise<void>;
  onChangeGroup: (id: string, group: string) => Promise<void>;
}) {
  if (categories.length === 0) {
    return <p className="text-muted-foreground text-sm">Nenhuma categoria cadastrada ainda.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {categories.map((category) => (
        <Card key={category.id}>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
            <p className="font-medium">
              {category.name}
              {category.is_archived && (
                <span className="text-muted-foreground text-sm font-normal"> · arquivada</span>
              )}
            </p>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground text-xs">Grupo no DRE</span>
                <Select
                  value={category.dre_group ?? NO_GROUP}
                  onValueChange={(value) => value && onChangeGroup(category.id, value)}
                  items={dreGroupOptions}
                >
                  <SelectTrigger className="w-48" aria-label={`Grupo no DRE de ${category.name}`}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {dreGroupOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {!category.is_archived && (
                <Button variant="outline" size="sm" onClick={() => onArchive(category.id)}>
                  Arquivar
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
