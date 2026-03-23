"use client";

import { Menu } from "lucide-react";
import { useEffect, useState } from "react";

import { SidebarNav } from "@/components/layout/app-shell-sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { useUserId } from "@/contexts/user-id-context";

export function TopBar() {
  const { userId, ready, setUserId } = useUserId();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");

  useEffect(() => {
    if (userId) setValue(userId);
  }, [userId]);

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:px-8">
      <div className="flex items-center md:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Open navigation"
            onClick={() => setOpen(true)}
          >
            <Menu className="size-5" />
          </Button>
          <SheetContent side="left" className="w-72 bg-sidebar p-0">
            <div className="border-b border-sidebar-border px-4 py-4">
              <span className="font-semibold">Orion Copilot</span>
            </div>
            <div className="p-3">
              <SidebarNav onNavigate={() => setOpen(false)} />
            </div>
          </SheetContent>
        </Sheet>
        <span className="ml-2 font-semibold md:hidden">Orion</span>
      </div>

      <div className="ml-auto flex max-w-md flex-1 flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-end">
        <Label
          htmlFor="user-id"
          className="sr-only sm:not-sr-only sm:w-24 shrink-0 text-xs text-muted-foreground"
        >
          User ID
        </Label>
        <Input
          id="user-id"
          className="h-9 font-mono text-xs"
          placeholder={ready ? "UUID" : "Loading…"}
          value={value}
          disabled={!ready}
          onChange={(e) => setValue(e.target.value)}
          onBlur={() => {
            if (value.trim()) setUserId(value.trim());
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && value.trim()) setUserId(value.trim());
          }}
        />
      </div>
    </header>
  );
}
