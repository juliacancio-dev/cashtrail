import { AppHeader } from "@/components/app-shell/app-header";

// Telas autenticadas: o cabeçalho com o menu fica aqui, uma vez só (doc 32, decisão 2).
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppHeader />
      {children}
    </>
  );
}
