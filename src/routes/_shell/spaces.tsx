import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { OwnerOrderBanner } from "@/components/owner-order-banner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusChip } from "@/components/truth-chip";
import { OWNER_ORDER } from "@/lib/admission";
import { CANONICAL_PUBLIC_SIX, SPACE_CONFIGS, spacePlan } from "@/lib/spaces";

export const Route = createFileRoute("/_shell/spaces")({
  component: SpacesPage,
});

function SpacesPage() {
  const plan = spacePlan();
  const canonical = SPACE_CONFIGS.filter((s) => s.canonical);
  const cells = SPACE_CONFIGS.filter((s) => s.vertical_id);
  const factory = SPACE_CONFIGS.find((s) => s.id.endsWith("/a11oy-factory"));

  return (
    <Page
      kicker="N7 Space release compiler"
      title="Hugging Face Spaces are configured. Hub is not mutated."
      lede="Six canonical surfaces, seven vertical cells, one protected factory bind. No Hugging Face token in this runtime — cards are ready, Spaces stay unpublished from here."
    >
      <OwnerOrderBanner />
      <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat k="Canonical six" v={String(CANONICAL_PUBLIC_SIX.length)} />
        <Stat k="Configured cards" v={String(SPACE_CONFIGS.length)} />
        <Stat k="Packet 6 Spaces" v={String(plan.inventory_count)} />
        <Stat k="Live org page" v="36" />
      </div>
      <p className="mt-3 text-xs text-subtle">{plan.live_org_observation.drift_note}</p>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Hub mutation</CardTitle>
          <CardDescription>
            {OWNER_ORDER.huggingface.intended_space} · {OWNER_ORDER.huggingface.status}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted">
          <p>{OWNER_ORDER.huggingface.blocker}</p>
          <p>
            Source of the factory card:{" "}
            <a className="text-accent underline-offset-4 hover:underline" href={OWNER_ORDER.github.url} rel="noreferrer" target="_blank">
              {OWNER_ORDER.github.factory_repo}
            </a>
          </p>
          <p>
            API:{" "}
            <a className="text-accent underline-offset-4 hover:underline" href="/api/a11oy/v1/spaces">
              /api/a11oy/v1/spaces
            </a>
          </p>
        </CardContent>
      </Card>

      <section className="mt-10">
        <h2 className="font-serif text-2xl tracking-tight">Canonical six</h2>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Lyte is on this list as the admitted commercial cell. Its visibility is protected, not public launch.
        </p>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {canonical.map((space) => (
            <SpaceCard key={space.id} space={space} />
          ))}
        </div>
      </section>

      {factory && (
        <section className="mt-10">
          <h2 className="font-serif text-2xl tracking-tight">Factory bind</h2>
          <div className="mt-4">
            <SpaceCard space={factory} />
          </div>
        </section>
      )}

      <section className="mt-10">
        <h2 className="font-serif text-2xl tracking-tight">Vertical cells</h2>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {cells.map((space) => (
            <SpaceCard key={space.id} space={space} />
          ))}
        </div>
      </section>

      <Card className="mt-10">
        <CardHeader>
          <CardTitle>Merge into Evidence Studio</CardTitle>
          <CardDescription>Packet 6 holographic / receipt Spaces. One writer later. Not deleted from here.</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {plan.merge_into_evidence_studio.map((id) => (
              <li key={id} className="font-mono text-xs text-muted">
                {id}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </Page>
  );
}

function SpaceCard({ space }: { space: (typeof SPACE_CONFIGS)[number] }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip value={space.publish} />
          <Badge variant={space.visibility === "public" ? "warn" : "default"}>{space.visibility}</Badge>
          {space.canonical ? <Badge>canonical</Badge> : null}
        </div>
        <CardTitle className="font-serif">{space.title}</CardTitle>
        <CardDescription className="font-mono text-xs">{space.id}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-muted">{space.card}</p>
        <p className="font-mono text-xs text-subtle">
          {space.sdk}
          {space.app_port ? `:${space.app_port}` : ""} · {space.hardware} · {space.recommended_action}
        </p>
        <ul className="space-y-1 text-xs text-subtle">
          {space.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="font-serif text-3xl tabular-nums">{v}</p>
      <p className="mt-1 text-xs uppercase tracking-wide text-subtle">{k}</p>
    </div>
  );
}
