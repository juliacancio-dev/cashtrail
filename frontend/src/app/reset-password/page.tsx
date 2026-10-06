"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { resetPassword } from "@/features/auth/api";
import { resetPasswordSchema, type ResetPasswordFormValues } from "@/features/auth/schemas";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  // Captura o token uma vez: o efeito abaixo o remove da URL.
  const [token] = useState(() => searchParams.get("token"));
  const [done, setDone] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    // Tira o token da barra de endereço/histórico para ele não vazar (ex: em print de tela).
    window.history.replaceState(null, "", window.location.pathname);
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema) });

  async function onSubmit(values: ResetPasswordFormValues) {
    if (!token) return;
    setFormError(null);
    try {
      await resetPassword(token, values.newPassword);
      setDone(true);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "erro ao redefinir a senha");
    }
  }

  if (!token) {
    return (
      <p className="text-sm">
        Link inválido.{" "}
        <Link href="/forgot-password" className="underline">
          Peça um novo link
        </Link>
        .
      </p>
    );
  }

  if (done) {
    return (
      <p className="text-sm">
        Senha redefinida. Por segurança, todas as sessões abertas foram encerradas.{" "}
        <Link href="/login" className="underline">
          Entrar com a nova senha
        </Link>
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="newPassword">Nova senha</Label>
        <Input id="newPassword" type="password" {...register("newPassword")} />
        {errors.newPassword && (
          <p className="text-sm text-destructive">{errors.newPassword.message}</p>
        )}
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="confirmPassword">Confirme a nova senha</Label>
        <Input id="confirmPassword" type="password" {...register("confirmPassword")} />
        {errors.confirmPassword && (
          <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
        )}
      </div>
      {formError && (
        <p className="text-sm text-destructive">
          {formError}{" "}
          <Link href="/forgot-password" className="underline">
            Pedir novo link
          </Link>
        </p>
      )}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Salvando..." : "Redefinir senha"}
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="flex flex-1 items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Criar nova senha</CardTitle>
        </CardHeader>
        <CardContent>
          {/* useSearchParams exige Suspense no static export (output: "export"). */}
          <Suspense fallback={<p className="text-sm text-muted-foreground">Carregando...</p>}>
            <ResetPasswordForm />
          </Suspense>
        </CardContent>
      </Card>
    </main>
  );
}
