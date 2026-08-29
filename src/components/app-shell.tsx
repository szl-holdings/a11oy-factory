import { useState, type ReactNode } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { profile } from "@/lib/data/registry";

const NAV = [
  { to: "/", label: "Product" },
  { to: "/admission", label: "Admission" },
  { to: "/frontier", label: "Frontier" },
  { to: "/console", label: "Console" },
  { to: "/investor", label: "Investor" },
  { to: "/estate", label: "Estate" },
  { to: "/spaces", label: "Spaces" },
  { to: "/trust", label: "Trust" },
  { to: "/verify", label: "Verify" },
] as const;

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <>
      {NAV.map((item) => {
        const active =
          item.to === "/"
            ? pathname === "/"
            : pathname === item.to || pathname.startsWith(`${item.to}/`);
        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={cn(
              "inline-flex h-11 items-center px-2 text-sm transition-colors duration-150",
              active ? "text-fg" : "text-muted hover:text-fg",
            )}
            aria-current={active ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-dvh bg-bg text-fg">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-accent focus:px-3 focus:py-2 focus:text-accent-fg"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b border-border bg-bg/90 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="font-serif text-xl tracking-tight">A11oy</span>
            <span className="hidden text-xs uppercase tracking-wide text-subtle sm:inline">
              control plane
            </span>
          </Link>
          <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary">
            <NavLinks />
          </nav>
          <div className="flex items-center gap-2">
            <span className="hidden rounded-full border border-fail/30 bg-fail/10 px-2.5 py-1 text-[11px] uppercase tracking-wide text-fail sm:inline">
              not production
            </span>
            <span className="hidden rounded-full border border-pass/30 bg-pass/10 px-2.5 py-1 text-[11px] uppercase tracking-wide text-pass md:inline">
              green light
            </span>
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open menu">
                  <Menu />
                </Button>
              </SheetTrigger>
              <SheetContent>
                <Link to="/" className="font-serif text-2xl" onClick={() => setOpen(false)}>
                  A11oy
                </Link>
                <nav className="mt-8 flex flex-col" aria-label="Mobile">
                  <NavLinks onNavigate={() => setOpen(false)} />
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>
      <div id="main">{children}</div>
      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-xs text-subtle sm:flex-row sm:items-center sm:justify-between">
          <p>
            Snapshot {profile.captured_at} · github.com/szl-holdings/a11oy-factory · HF Space published private
          </p>
          <div className="flex flex-wrap gap-4">
            <a
              href="https://github.com/szl-holdings/a11oy-factory"
              className="hover:text-fg"
              rel="noreferrer"
              target="_blank"
            >
              GitHub
            </a>
            <Link to="/admission" className="hover:text-fg">
              Admission
            </Link>
            <Link to="/frontier" className="hover:text-fg">
              Frontier
            </Link>
            <Link to="/research" className="hover:text-fg">
              Research
            </Link>
            <Link to="/killinchu" className="hover:text-fg">
              Killinchu
            </Link>
            <Link to="/company" className="hover:text-fg">
              Company
            </Link>
            <Link to="/trust" className="hover:text-fg">
              Trust
            </Link>
            <a href="/api/a11oy/v1/admission" className="hover:text-fg">
              Admission order
            </a>
            <a href="/api/a11oy/v1/honest" className="hover:text-fg">
              Honest contract
            </a>
            <a href="/healthz" className="hover:text-fg">
              healthz
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export function Page({
  kicker,
  title,
  lede,
  children,
}: {
  kicker?: string;
  title: string;
  lede?: string;
  children: ReactNode;
}) {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:py-14">
      <header className="max-w-3xl">
        {kicker && (
          <p className="text-xs uppercase tracking-[0.18em] text-subtle">{kicker}</p>
        )}
        <h1 className="mt-3 font-serif text-4xl tracking-tight text-balance sm:text-5xl">{title}</h1>
        {lede && <p className="mt-4 max-w-2xl text-pretty text-muted">{lede}</p>}
      </header>
      <div className="mt-10">{children}</div>
    </main>
  );
}
