import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { OwnerOrderBanner } from "@/components/owner-order-banner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PriorityChip, StatusChip } from "@/components/truth-chip";
import { OWNER_ORDER } from "@/lib/admission";
import { profile } from "@/lib/data/registry";
import { formatKb } from "@/lib/utils";

export const Route = createFileRoute("/_shell/estate")({
  component: EstatePage,
});

function EstatePage() {
  return (
    <Page
      kicker="Canonical technical estate"
      title="One generated home"
      lede="Packet 6 remains the captured inventory. Owner overlay is live on GitHub: freeze lifted, nexus classified, factory published as an A11oy package."
    >
      <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat k="Authenticated repos" v={profile.counts.github_repositories_authenticated} />
        <Stat k="Public GitHub page" v={profile.counts.github_public_page_displayed} />
        <Stat k="Hub Spaces" v={profile.counts.hf_spaces} />
        <Stat k="/spaces display" v={profile.counts.a11oy_spaces_route_displayed} />
      </div>
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>szl-holdings alignment</CardTitle>
          <CardDescription>Live GitHub overlay on Packet 6. Hub Space exists; Docker is fetching metadata. a-11-oy.com is not certified.</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted">
            <li>
              <a className="text-accent underline-offset-4 hover:underline" href="https://github.com/szl-holdings/a11oy-factory" rel="noreferrer" target="_blank">szl-holdings/a11oy-factory</a>
              {" "}— public BIND_AS_A11OY_PACKAGE · CI green on main
            </li>
            <li>
              <a className="text-accent underline-offset-4 hover:underline" href="https://github.com/szl-holdings/nexus" rel="noreferrer" target="_blank">szl-holdings/nexus</a>
              {" "}— classified A11OY_INCUBATOR_PACKAGE · not a second flagship
            </li>
            <li>
              <a className="text-accent underline-offset-4 hover:underline" href="https://huggingface.co/spaces/SZLHOLDINGS/a11oy-factory" rel="noreferrer" target="_blank">SZLHOLDINGS/a11oy-factory</a>
              {" "}— published private via szl-experiments · not a seventh public Space
            </li>
            <li>
              <a className="text-accent underline-offset-4 hover:underline" href="https://github.com/szl-holdings/a11oy/issues/1426" rel="noreferrer" target="_blank">a11oy#1426</a>
              {" "}— bind-the-factory tracking
            </li>
          </ul>
        </CardContent>
      </Card>
      <Tabs defaultValue="repos">
        <TabsList className="flex w-full flex-wrap justify-start">
          <TabsTrigger value="repos">Repositories</TabsTrigger>
          <TabsTrigger value="hub">Hugging Face</TabsTrigger>
          <TabsTrigger value="routes">A11oy routes</TabsTrigger>
          <TabsTrigger value="freeze">Admission freeze</TabsTrigger>
        </TabsList>
        <TabsContent value="repos">
          <RepoTable />
        </TabsContent>
        <TabsContent value="hub">
          <HubTable />
        </TabsContent>
        <TabsContent value="routes">
          <RouteTable />
        </TabsContent>
        <TabsContent value="freeze">
          <Freeze />
        </TabsContent>
      </Tabs>
    </Page>
  );
}

function Stat({ k, v }: { k: string; v: number }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="font-serif text-3xl tabular-nums">{v}</p>
      <p className="mt-1 text-xs uppercase tracking-wide text-subtle">{k}</p>
    </div>
  );
}

function RepoTable() {
  const [q, setQ] = useState("");
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return profile.repositories.filter((row) =>
      !needle
        ? true
        : [row.repository, row.recommended_action, row.target_class, row.priority]
            .join(" ")
            .toLowerCase()
            .includes(needle),
    );
  }, [q]);
  return (
    <Card>
      <CardHeader>
        <CardTitle>77-row one-by-one</CardTitle>
        <CardDescription>
          szl-holdings/nexus is classified as an A11oy incubator package. Packet 6 captured it as BLOCK_AND_CLASSIFY. Authenticated inventory is 77.
        </CardDescription>
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter repositories"
          aria-label="Filter repositories"
        />
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-subtle">
            <tr>
              <th className="py-2 pr-3">Repository</th>
              <th className="py-2 pr-3">Vis</th>
              <th className="py-2 pr-3">Action</th>
              <th className="py-2 pr-3">P</th>
              <th className="py-2">Size</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.repository}
                className={
                  row.repository === "szl-holdings/nexus"
                    ? "border-t border-pass/40 bg-pass/5"
                    : "border-t border-border"
                }
              >
                <td className="py-2 pr-3 font-mono text-xs">
                  {row.repository}
                  {row.repository === "szl-holdings/nexus" ? (
                    <span className="ml-2 text-pass">classified</span>
                  ) : (
                    row.new_since_payload4 && <span className="ml-2 text-fail">new</span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {row.visibility}
                  {row.archived ? " / archived" : ""}
                </td>
                <td className="py-2 pr-3">
                  <StatusChip value={row.recommended_action} />
                </td>
                <td className="py-2 pr-3">
                  <PriorityChip value={row.priority} />
                </td>
                <td className="py-2 text-muted">{formatKb(row.size_kb_captured)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function HubTable() {
  const [q, setQ] = useState("");
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return profile.hugging_face_assets.filter((row) =>
      !needle
        ? true
        : [row.asset_id, row.category, row.recommended_action].join(" ").toLowerCase().includes(needle),
    );
  }, [q]);
  return (
    <Card>
      <CardHeader>
        <CardTitle>99 Hub assets</CardTitle>
        <CardDescription>
          Target: six canonical public Spaces. Drift: Hub reports 27 Spaces, A11oy /spaces showed 26.
        </CardDescription>
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter assets" aria-label="Filter Hub assets" />
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-subtle">
            <tr>
              <th className="py-2 pr-3">Asset</th>
              <th className="py-2 pr-3">Kind</th>
              <th className="py-2 pr-3">Action</th>
              <th className="py-2">P</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.category}:${row.asset_id}`} className="border-t border-border align-top">
                <td className="py-2 pr-3 font-mono text-xs">{row.asset_id}</td>
                <td className="py-2 pr-3">{row.category}</td>
                <td className="py-2 pr-3">
                  <StatusChip value={row.recommended_action} />
                </td>
                <td className="py-2">
                  <PriorityChip value={row.priority} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function RouteTable() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>33 route contracts</CardTitle>
        <CardDescription>Every public tab needs owner, purpose, source, status, a11y, tests, deprecation.</CardDescription>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-subtle">
            <tr>
              <th className="py-2 pr-3">Route</th>
              <th className="py-2 pr-3">State</th>
              <th className="py-2 pr-3">Target</th>
              <th className="py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {profile.a11oy_routes.map((row) => (
              <tr key={row.route} className="border-t border-border align-top">
                <td className="py-2 pr-3 font-mono text-xs">{row.route}</td>
                <td className="py-2 pr-3">
                  <StatusChip value={row.captured_state} />
                </td>
                <td className="py-2 pr-3 text-muted">{row.target_route}</td>
                <td className="py-2">
                  <PriorityChip value={row.priority} /> {row.recommended_action}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function Freeze() {
  const freeze = profile.admission_freeze;
  return (
    <div className="space-y-4">
      <OwnerOrderBanner />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Packet 6 freeze — historical</CardTitle>
            <CardDescription>{freeze.reason}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-xs uppercase tracking-wide text-subtle">Then blocked</p>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              {freeze.blocks.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="mt-4 text-xs uppercase tracking-wide text-subtle">Exit evidence named</p>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              {freeze.exit.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Current overlay</CardTitle>
            <CardDescription>
              {OWNER_ORDER.effects.freeze} · nexus {OWNER_ORDER.effects.nexus.classification}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted">{OWNER_ORDER.effects.nexus.note}</p>
            <p className="mt-3 text-xs uppercase tracking-wide text-subtle">Still closed</p>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              {OWNER_ORDER.still_prohibits.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="mt-4 text-xs uppercase tracking-wide text-subtle">
              Six canonical public Spaces
            </p>
            <ol className="mt-2 space-y-2">
              {profile.canonical_public_spaces_target.map((item) => (
                <li key={item} className="font-mono text-xs">
                  {item}
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
