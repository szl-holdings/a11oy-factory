import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DecisionTheatre } from "@/components/decision-theatre";
import { OwnerOrderBanner } from "@/components/owner-order-banner";
import { StatusChip } from "@/components/truth-chip";
import { cellOverlay } from "@/lib/admission";
import { profile, verticalById } from "@/lib/data/registry";

export const Route = createFileRoute("/_shell/")({
  component: Home,
});

function Home() {
  const lyte = verticalById("lyte-services")!;
  const lyteOverlay = cellOverlay("lyte-services");
  return (
    <main>
      <section className="border-b border-border">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:py-24 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-subtle">
              Lyte Services · admitted protected pilot
            </p>
            <h1 className="mt-4 font-serif text-4xl tracking-tight text-balance sm:text-6xl">
              Green light approved. Frontiers are open.
            </h1>
            <p className="mt-5 max-w-xl text-pretty text-lg text-muted">
              The estate owner approved the green light. Nexus is classified as an A11oy incubator
              package. Lyte is the first admitted cell. N1–N8 runs on the same Decision Cell
              Compiler — not seven public forks.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild>
                <Link to="/frontier">
                  Open frontier program
                  <ArrowRight />
                </Link>
              </Button>
              <Button variant="secondary" asChild>
                <Link to="/verticals/$id" params={{ id: "lyte-services" }}>
                  Run a Lyte scenario
                </Link>
              </Button>
            </div>
            <p className="mt-6 max-w-xl text-sm text-subtle">
              Source is public at szl-holdings/a11oy-factory. a-11-oy.com is certified LIVE_PRODUCT_ORIGIN. Signer ABSENT. FedRAMP uncertified. Formulas never grant authority.
            </p>
          </div>
          <div className="space-y-4">
            <OwnerOrderBanner compact />
            <Card>
              <CardHeader>
                <CardTitle>What the buyer sees</CardTitle>
                <CardDescription>{lyte.decision_problem}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted">
                {lyte.core_workflows.map((item) => (
                  <div key={item} className="border-t border-border pt-3 first:border-0 first:pt-0">
                    {item}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["APPROVED", "owner green light"],
            ["CLASSIFIED", "nexus as A11oy incubator"],
            ["ADMITTED", "Lyte protected pilot"],
            ["OPEN", "frontier N1–N8"],
          ].map(([stat, label]) => (
            <div key={label} className="rounded-xl border border-border bg-surface p-4">
              <p className="font-serif text-3xl tracking-tight">{stat}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-subtle">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="font-serif text-3xl tracking-tight">Admitted cell — Lyte</h2>
            <p className="mt-2 text-sm text-muted">
              {lyteOverlay.label}. Public launch remains blocked until measured pilot evidence.
            </p>
          </div>
          <Link
            to="/verticals/$id"
            params={{ id: "lyte-services" }}
            className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
          >
            Open Lyte cell
          </Link>
        </div>
        <DecisionTheatre vertical={lyte} autoSelect="lyte-aether-msa" />
      </section>

      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="font-serif text-3xl tracking-tight">Seven manifests, one runtime</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Do not create seven public forks. Each vertical is a configuration of the Decision Cell
            Compiler.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {profile.vertical_cells.map((cell) => {
              const overlay = cellOverlay(cell.vertical_id);
              return (
                <Link
                  key={cell.vertical_id}
                  to="/verticals/$id"
                  params={{ id: cell.vertical_id }}
                  className="rounded-xl border border-border bg-surface p-5 transition-colors hover:border-accent/40"
                >
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-serif text-xl tracking-tight">
                      {cell.display_name.split("—")[0]}
                    </h3>
                    <StatusChip value={overlay.admitted ? "ADMITTED" : cell.space_visibility} />
                  </div>
                  <p className="mt-2 text-sm text-muted">{overlay.label}</p>
                  <p className="mt-3 line-clamp-3 text-sm text-subtle">{cell.buyer}</p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>
    </main>
  );
}
