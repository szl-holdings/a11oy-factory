import { createFileRoute, Link } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DecisionTheatre } from "@/components/decision-theatre";
import { investorDemo } from "@/lib/compiler";
import { profile, snapshot } from "@/lib/data/registry";
import { verticalById } from "@/lib/data/registry";

export const Route = createFileRoute("/_shell/investor")({
  component: InvestorPage,
});

function InvestorPage() {
  const lyte = verticalById("lyte-services")!;
  const demo = investorDemo(lyte);
  return (
    <Page
      kicker="Diligence"
      title="Three-minute investor proof"
      lede="The narrative is compiled from the same release and receipt contracts as the product. No hand-edited metrics."
    >
      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {demo.three_minute_sequence.map((step) => (
          <li key={step.step} className="rounded-xl border border-border bg-surface p-4">
            <p className="font-mono text-xs text-subtle">{String(step.step).padStart(2, "0")}</p>
            <h2 className="mt-2 font-serif text-lg tracking-tight">{step.show}</h2>
            <p className="mt-2 text-sm text-muted">
              {Array.isArray(step.content) ? step.content.join(" · ") : String(step.content)}
            </p>
          </li>
        ))}
      </ol>

      <div className="mt-10 grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Problem</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted">{lyte.decision_problem}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Buyer</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted">{lyte.buyer}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Control</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted">
            {profile.product_hierarchy.core_product.one_sentence}
          </CardContent>
        </Card>
      </div>

      <div className="mt-12">
        <h2 className="font-serif text-3xl tracking-tight">Positive and negative demo</h2>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Record a renewal proposal, then switch to the Northwind margin miss or missing discovery.
          Both write the same ledger.
        </p>
        <div className="mt-6">
          <DecisionTheatre vertical={lyte} />
        </div>
      </div>

      <div className="mt-12 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Traction — current evidence only</CardTitle>
            <CardDescription>Packet 6 snapshot. Not a customer claim.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted">
            <p>Lyte: admitted protected design-partner cell. Public launch still needs measured pilot evidence.</p>
            <p>Open PRs: {profile.counts.open_prs_authenticated} (down from a larger DAG).</p>
            <p>Admission freeze lifted by owner order AO-2026-08-29-001. Public repos, Spaces, and product names stay closed.</p>
            <p>Killinchu public Space: EPHEMERAL, production_ready=false.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Risks</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted">
              {snapshot.material_findings.slice(0, 6).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Button asChild>
          <Link to="/trust">Diligence / trust index</Link>
        </Button>
        <Button variant="secondary" asChild>
          <Link to="/frontier">Frontier program</Link>
        </Button>
      </div>
      <p className="mt-6 text-xs text-subtle">{demo.claims_boundary}</p>
    </Page>
  );
}
