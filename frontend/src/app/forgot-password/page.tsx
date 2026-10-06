"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { requestPasswordReset } from "@/features/auth/api";
import { forgotPasswordSchema, type ForgotPasswordFormValues } from "@/features/auth/schemas";

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormValues>({ resolver: zodResolver(forgotPasswordSchema) });

  async function onSubmit(values: ForgotPasswordFormValues) {
    setFormError(null);
    try {
      await requestPasswordReset(values.email);
      setSubmitted(true);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "erro ao solicitar redefinição de senha");
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Esqueci minha senha</CardTitle>
        </CardHeader>
        <CardContent>
          {submitted ? (
            // Mesma mensagem exista ou não a conta (RF-013, não revela e-mails cadastrados).
            <p className="text-sm">
              Se o e-mail estiver cadastrado, você vai receber um link para criar uma nova senha. O
              link expira em 30 minutos.
            </p>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="email">E-mail</Label>
                <Input id="email" type="email" {...register("email")} />
                {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
              </div>
              {formError && <p className="text-sm text-destructive">{formError}</p>}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Enviando..." : "Enviar link"}
              </Button>
            </form>
          )}
          <p className="mt-4 text-sm text-muted-foreground">
            <Link href="/login" className="underline">
              Voltar para o login
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
