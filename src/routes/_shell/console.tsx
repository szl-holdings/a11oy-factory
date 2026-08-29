import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { StatusChip, PriorityChip } from "@/components/truth-chip";
import { profile, snapshot } from "@/lib/data/registry";
import { genome } from "@/lib/honest";
import { evaluatePolicy, shadowCompare } from "@/lib/policy";
import { scenarios } from "@/lib/scenarios";
import { verticalById } from "@/lib/data/registry";
import { organCatalog } from "@/lib/organs";
import { loadOrganLedger } from "@/lib/organ-ledger";

export const Route = createFileRoute("/_shell/console")({
  component: ConsolePage,
});

function ConsolePage() {
  return (
    <Page
      kicker="Operator"
      title="Console"
      lede="Separate from the investor journey. Claims here are evidence-scoped. Nothing on this page is a production certification."
    >
      <Tabs defaultValue="overview">
        <TabsList className="flex w-full flex-wrap justify-start">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="observability">Observability</TabsTrigger>
          <TabsTrigger value="policy">Policy lab</TabsTrigger>
          <TabsTrigger value="organs">Organs</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          <Overview />
        </TabsContent>
        <TabsContent value="observability">
          <Observability />
        </TabsContent>
        <TabsContent value="policy">
          <PolicyLab />
        </TabsContent>
        <TabsContent value="organs">
          <OrganApi />
        </TabsContent>
      </Tabs>
    </Page>
  );
}

function Overview() {
  const p0 = profile.a11oy_routes.filter((r) => r.priority === "P0");
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Open pull requests</CardTitle>
          <CardDescription>Three remain. None of them certify production.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {profile.current_open_prs.map((pr) => (
            <div key={`${pr.repository}-${pr.number}`} className="border-t border-border pt-3 first:border-0 first:pt-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-subtle">
                  {pr.repository}#{pr.number}
                </span>
                <StatusChip value={pr.disposition} />
              </div>
              <p className="mt-1 text-sm">{pr.title}</p>
              <p className="mt-1 text-sm text-muted">{pr.reason}</p>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>P0 route work</CardTitle>
          <CardDescription>{p0.length} routes still require evidence-scoped repair.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {p0.slice(0, 8).map((route) => (
            <div key={route.route} className="flex items-start justify-between gap-3 border-t border-border pt-3 first:border-0 first:pt-0">
              <div>
                <p className="font-mono text-sm">{route.route}</p>
                <p className="text-xs text-muted">{route.recommended_action}</p>
              </div>
              <PriorityChip value={route.priority} />
            </div>
          ))}
          <Link to="/estate" className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline">
            Full route matrix
          </Link>
        </CardContent>
      </Card>
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Material findings</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted">
            {snapshot.material_findings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

function Observability() {
  const g = genome();
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Exact counts — no cross-route drift</CardTitle>
          <CardDescription>
            Observability must not say every span is signed, 9 proved Lambda axes, or 5 proved formulas.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat k="Locked-proved formulas" v="8" />
          <Stat k="Catalogue (incl. advisory)" v={String(g.catalogue_count)} />
          <Stat k="Lambda proved axes" v="0" />
          <Stat k="Lambda advisory axes" v="13" />
          <Stat k="Span signing" v="not every span" />
          <Stat k="OTel" v="bind claims to evidence" />
          <Stat k="Persistence" v="localStorage durable" />
          <Stat k="Signer" v="unsigned-preview" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Formula genome</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-subtle">
              <tr>
                <th className="py-2 pr-3">ID</th>
                <th className="py-2 pr-3">Class</th>
                <th className="py-2 pr-3">Grants authority</th>
                <th className="py-2">Prohibited claim</th>
              </tr>
            </thead>
            <tbody>
              {g.formulas.map((f) => (
                <tr key={f.formula_id} className="border-t border-border align-top">
                  <td className="py-2 pr-3 font-mono">{f.formula_id}</td>
                  <td className="py-2 pr-3">
                    <Badge variant={f.proof_class.startsWith("LOCKED") ? "pass" : "warn"}>
                      {f.proof_class}
                    </Badge>
                  </td>
                  <td className="py-2 pr-3">{String(f.grants_authority)}</td>
                  <td className="py-2 text-muted">{f.prohibited_claim}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function PolicyLab() {
  const [id, setId] = useState(scenarios[0].scenario_id);
  const scenario = scenarios.find((s) => s.scenario_id === id)!;
  const vertical = verticalById(scenario.vertical_id)!;
  const run = useMemo(() => shadowCompare(vertical, scenario), [vertical, scenario]);
  const current = evaluatePolicy(vertical, scenario, "LOG_ONLY");
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Shadow comparison</CardTitle>
          <CardDescription>
            Candidate policy runs LOG_ONLY. It never mutates authority. Promotion would require an exact
            diff, review, and runtime readback.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <select
            className="h-11 w-full rounded-lg border border-border bg-elevated px-3 text-sm"
            value={id}
            onChange={(e) => setId(e.target.value)}
          >
            {scenarios.map((item) => (
              <option key={item.scenario_id} value={item.scenario_id}>
                {item.vertical_id} — {item.title}
              </option>
            ))}
          </select>
          <p className="text-sm text-muted">{scenario.summary}</p>
          <div className="flex flex-wrap gap-2">
            <span className="text-xs uppercase tracking-wide text-subtle">current</span>
            <StatusChip value={current.effect} />
            <span className="text-xs uppercase tracking-wide text-subtle">candidate</span>
            <StatusChip value={run.candidate.effect} />
            {run.differs ? (
              <Badge variant="warn">differs</Badge>
            ) : (
              <Badge>no delta</Badge>
            )}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Reasons</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs uppercase tracking-wide text-subtle">Current</p>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              {run.current.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-subtle">Candidate</p>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              {run.candidate.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function OrganApi() {
  const catalog = organCatalog();
  const ledger = loadOrganLedger();
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Organ API</CardTitle>
          <CardDescription>
            Workbench POSTs the same contract the catalog publishes. Not 25 public Spaces.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 font-mono text-xs text-muted">
          {catalog.endpoints.map((item) => (
            <p key={`${item.method}-${item.path}`}>
              {item.method} {item.path}
            </p>
          ))}
          <Link to="/frontier" className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline">
            Open N1–N25 workbench
          </Link>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Browser organ ledger</CardTitle>
          <CardDescription>{ledger.entries.length} receipt{ledger.entries.length === 1 ? "" : "s"} in this browser.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {ledger.entries.slice(-8).reverse().map((item) => (
            <div key={item.hash} className="flex flex-wrap items-center gap-2 border-t border-border pt-3 first:border-0 first:pt-0">
              <StatusChip value={item.status} />
              <span className="font-mono text-xs">{item.id}</span>
              <span className="text-sm">{item.title}</span>
            </div>
          ))}
          {ledger.entries.length === 0 && <p className="text-sm text-muted">Run an organ on Frontier to append a receipt.</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-lg border border-border bg-elevated p-3">
      <p className="font-serif text-2xl tabular-nums">{v}</p>
      <p className="mt-1 text-xs uppercase tracking-wide text-subtle">{k}</p>
    </div>
  );
}
