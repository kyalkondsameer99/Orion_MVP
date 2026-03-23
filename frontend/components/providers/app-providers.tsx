"use client";

import { Toaster } from "@/components/ui/sonner";
import { UserIdProvider } from "@/contexts/user-id-context";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <UserIdProvider>
      {children}
      <Toaster richColors position="top-right" />
    </UserIdProvider>
  );
}
