"use client";

import { LayoutDashboard, LineChart, ListOrdered, ListPlus, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/watchlist", label: "Watchlist", icon: ListPlus },
  { href: "/recommendations", label: "Recommendations", icon: LineChart },
  { href: "/orders", label: "Orders", icon: ListOrdered },
  { href: "/positions", label: "Positions", icon: Wallet },
];

export function SidebarNav({
  onNavigate,
  className,
}: {
  onNavigate?: () => void;
  className?: string;
}) {
  const pathname = usePathname();
  return (
    <nav className={cn("flex flex-col gap-1", className)}>
      {nav.map(({ href, label, icon: Icon }) => {
        const active =
          href === "/"
            ? pathname === "/"
            : pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="size-4 shrink-0 opacity-80" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShellSidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-border bg-sidebar md:flex md:flex-col">
      <div className="flex h-14 items-center border-b border-sidebar-border px-6">
        <Link href="/" className="font-semibold tracking-tight">
          Orion Copilot
        </Link>
      </div>
      <ScrollArea className="flex-1 px-3 py-4">
        <SidebarNav />
      </ScrollArea>
      <Separator />
      <div className="p-4 text-xs text-muted-foreground">
        Paper trading · AI-assisted signals
      </div>
    </aside>
  );
}
