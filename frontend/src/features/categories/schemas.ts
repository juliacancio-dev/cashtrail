import { z } from "zod";

export const createCategorySchema = z.object({
  name: z.string().min(1, "informe um nome"),
});

export type CreateCategoryFormValues = z.infer<typeof createCategorySchema>;

export type Category = {
  id: string;
  name: string;
  is_archived: boolean;
  created_at: string;
};
