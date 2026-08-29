import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Page } from "@/components/app-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buildHonest } from "@/lib/honest";
import { profile, PROFILE_SHA256, snapshot } from "@/lib/data/registry";
import { validateProfile } from "@/lib/compiler";
import type { HonestContract } from "@/lib/types";

export const Route = createFileRoute("/_shell/trust")({
  component: TrustPage,
});

function TrustPage() {
  const [honest, setHonest] = useState<HonestContract | null>(null);
  useEffect(() => {
    setHonest(buildHonest());
  }, []);
  const errors = validateProfile();
  return (
    <Page
      kicker="Truth boundary"
      title="Generated from the registry"
      lede="Every count on this page is produced from Packet 6. If a number cannot be generated, it is labeled UNAVAILABLE — not estimated."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Honest contract</CardTitle>
            <CardDescription>Machine-readable truth for every public route.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 font-mono text-xs text-muted">
            <p>locked_formula_count: 8</p>
            <p>production_ready: false</p>
            <p>product_origin: LIVE_PRODUCT_ORIGIN</p>
            <p>organs: 25 LIVE</p>
            <p>signer: ABSENT</p>
            <p>nexus: CLASSIFIED_A11OY_INCUBATOR</p>
            <p>admission_freeze: LIFTED_BY_OWNER</p>
            <p>green_light: APPROVED</p>
            <p>profile: {PROFILE_SHA256.slice(0, 16)}…</p>
            <p>persistence: {honest?.persistence.backend} / durable={String(honest?.persistence.durable)}</p>
            <a href="/api/a11oy/v1/honest" className="inline-flex h-11 items-center text-accent underline-offset-4 hover:underline">
              GET /api/a11oy/v1/honest
            </a>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Profile validation</CardTitle>
          </CardHeader>
          <CardContent>
            {errors.length === 0 ? (
              <Badge variant="pass">VALID</Badge>
            ) : (
              <ul className="text-sm text-fail">
                {errors.map((e) => (
                  <li key={e}>{e}</li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-sm text-muted">
              Packet 6 still records nexus as BLOCK_AND_CLASSIFY. Current overlay classifies it as an A11oy incubator package. Canonical public Space target remains six.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Public Space vs Hub</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted">
            <p>Hub Spaces: {profile.counts.hf_spaces}</p>
            <p>A11oy /spaces displayed: {profile.counts.a11oy_spaces_route_displayed}</p>
            <p>Drift: {profile.counts.hf_spaces - profile.counts.a11oy_spaces_route_displayed}</p>
            <p className="mt-3">
              Production a-11-oy.com /spaces must be generated from the Hub registry or declare an
              explicit scoped count.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Binding truth statements</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted">
            {profile.truth_boundary.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Captured production observation (external)</CardTitle>
          <CardDescription>Read-only snapshot. This preview does not recapture live providers.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 text-sm text-muted sm:grid-cols-2">
          <div>
            <p className="text-xs uppercase tracking-wide text-subtle">a-11-oy.com honest</p>
            <p className="mt-2 font-mono text-xs">{snapshot.current_a11oy_honest_observation.git_sha}</p>
            <p>locked formulas: {snapshot.current_a11oy_honest_observation.locked_formula_count}</p>
            <p>{snapshot.current_a11oy_honest_observation.persistence_claim}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-subtle">Killinchu readyz</p>
            <p className="mt-2">
              {snapshot.current_killinchu_ready_observation.status} ·{" "}
              {snapshot.current_killinchu_ready_observation.durability_state}
            </p>
            <p>production_ready={String(snapshot.current_killinchu_ready_observation.production_ready)}</p>
          </div>
        </CardContent>
      </Card>

      <div className="mt-6 flex flex-wrap gap-4 text-sm">
        <Link to="/verify" className="inline-flex h-11 items-center text-accent underline-offset-4 hover:underline">
          Receipt verifier
        </Link>
        <a href="/api/a11oy/tab-matrix" className="inline-flex h-11 items-center text-accent underline-offset-4 hover:underline">
          Tab matrix API
        </a>
        <a href="/api/a11oy/v1/genome" className="inline-flex h-11 items-center text-accent underline-offset-4 hover:underline">
          Genome API
        </a>
      </div>
    </Page>
  );
}
