import { createFileRoute, Link } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { KillinchuSim } from "@/components/killinchu-sim";
import { DecisionTheatre } from "@/components/decision-theatre";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { profile, snapshot, verticalById } from "@/lib/data/registry";

export const Route = createFileRoute("/_shell/killinchu")({
  component: KillinchuPage,
});

function KillinchuPage() {
  const cell = verticalById("killinchu")!;
  return (
    <Page
      kicker="Public high-stakes reference"
      title="Killinchu — simulated proposal system"
      lede="Software stops at recommendation, denial, or escalation. Physical authority remains outside the public system."
    >
      <div className="mb-6 flex flex-wrap gap-2">
        <Badge variant="warn">SIMULATED</Badge>
        <Badge variant="warn">proposal-only</Badge>
        <Badge variant="fail">no physical effector</Badge>
        <Badge variant="fail">
          public Space {snapshot.current_killinchu_ready_observation.durability_state}
        </Badge>
      </div>
      <KillinchuSim />
      <div className="mt-12">
        <h2 className="font-serif text-3xl tracking-tight">Decision receipts</h2>
        <p className="mt-2 text-sm text-muted">
          Human decision is mandatory. Missing provenance denies. A request that implies an effector
          is denied and receipted.
        </p>
        <div className="mt-6">
          <DecisionTheatre vertical={cell} autoSelect="killinchu-geofence-ok" />
        </div>
      </div>
      <Card className="mt-10">
        <CardHeader>
          <CardTitle>Public surface audit</CardTitle>
          <CardDescription>Packet 6 captured findings. This preview does not repair the live Space.</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-subtle">
              <tr>
                <th className="py-2 pr-3">Route</th>
                <th className="py-2 pr-3">Role</th>
                <th className="py-2">Finding</th>
              </tr>
            </thead>
            <tbody>
              {profile.killinchu_routes.map((row) => (
                <tr key={row.route} className="border-t border-border align-top">
                  <td className="py-2 pr-3 font-mono text-xs">{row.route}</td>
                  <td className="py-2 pr-3">{row.role}</td>
                  <td className="py-2 text-muted">{row.finding}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
      <p className="mt-6 text-sm">
        <Link to="/verticals/$id" params={{ id: "killinchu" }} className="text-accent underline-offset-4 hover:underline">
          Compiled Killinchu cell
        </Link>
      </p>
    </Page>
  );
}
