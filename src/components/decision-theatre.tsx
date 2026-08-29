import { useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EffectChip, EvidenceChip, TruthStrip } from "@/components/truth-chip";
import { ReceiptCard } from "@/components/receipt-card";
import { compileVertical } from "@/lib/compiler";
import { formulaIds } from "@/lib/data/registry";
import { liveScenariosFor } from "@/lib/forge";
import { appendDecision } from "@/lib/ledger";
import { evaluatePolicy, shadowCompare } from "@/lib/policy";
import type { DecisionReceipt, Scenario, VerticalCell } from "@/lib/types";

export function DecisionTheatre({
  vertical,
  autoSelect,
}: {
  vertical: VerticalCell;
  autoSelect?: string;
}) {
  const list = liveScenariosFor(vertical.vertical_id);
  const [scenarioId, setScenarioId] = useState(autoSelect ?? list[0]?.scenario_id);
  const [actor, setActor] = useState(vertical.human_authority[0] ?? "named operator");
  const [receipt, setReceipt] = useState<DecisionReceipt | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shadow, setShadow] = useState(true);

  const scenario = useMemo(
    () => list.find((item) => item.scenario_id === scenarioId) ?? list[0],
    [list, scenarioId],
  );

  if (!scenario) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No synthetic scenarios</CardTitle>
          <CardDescription>This cell has no rights-cleared fixtures yet.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const current = evaluatePolicy(vertical, scenario, "LOG_ONLY");
  const shadowRun = shadowCompare(vertical, scenario);

  async function run(approve: boolean) {
    setBusy(true);
    setError(null);
    try {
      const compiled = await compileVertical(vertical, formulaIds());
      const next = await appendDecision({
        vertical,
        scenario: scenario as Scenario,
        actor,
        approve,
        manifestDigest: compiled.manifest_digest,
        includeShadow: shadow,
      });
      setReceipt(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "decision failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Governed scenario</CardTitle>
          <CardDescription>
            Policy mode is LOG_ONLY. A proposal cannot grant authority. External action stays outside this runtime.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="block">
            <span className="text-xs uppercase tracking-wide text-muted">Scenario</span>
            <select
              className="mt-1 h-11 w-full rounded-lg border border-border bg-elevated px-3 text-sm"
              value={scenario.scenario_id}
              onChange={(e) => {
                setScenarioId(e.target.value);
                setReceipt(null);
              }}
            >
              {list.map((item) => (
                <option key={item.scenario_id} value={item.scenario_id}>
                  {item.negative ? "Negative — " : "Positive — "}
                  {item.title}
                </option>
              ))}
            </select>
          </label>
          <p className="text-pretty text-sm text-muted">{scenario.summary}</p>
          <div className="flex flex-wrap gap-1.5">
            {scenario.evidence.map((item) => (
              <span key={item.evidence_id} className="inline-flex items-center gap-1.5">
                <EvidenceChip value={item.class} />
                <span className="text-xs text-muted">{item.label}</span>
              </span>
            ))}
          </div>
          <TruthStrip
            evidence={scenario.evidence[0]?.class ?? "UNAVAILABLE"}
            runtime="factory preview / LOG_ONLY"
            authority="human required"
            freshness={scenario.evidence[0]?.freshness ?? "unknown"}
            limitations="synthetic; no production claim"
          />
          <div className="rounded-lg border border-border bg-elevated p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs uppercase tracking-wide text-subtle">Current effect</span>
              <EffectChip value={current.effect} />
              <span className="text-xs uppercase tracking-wide text-subtle">Candidate shadow</span>
              <EffectChip value={shadowRun.candidate.effect} />
              {shadowRun.differs ? (
                <span className="text-xs text-warn">differs — still LOG_ONLY</span>
              ) : (
                <span className="text-xs text-subtle">no delta</span>
              )}
            </div>
            <ul className="mt-3 space-y-1 text-sm text-muted">
              {current.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
          <label className="flex min-h-11 items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={shadow}
              onChange={(e) => setShadow(e.target.checked)}
              className="size-4 accent-accent"
            />
            Attach candidate-policy shadow comparison
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-wide text-muted">Human authority</span>
            <select
              className="mt-1 h-11 w-full rounded-lg border border-border bg-elevated px-3 text-sm"
              value={actor}
              onChange={(e) => setActor(e.target.value)}
            >
              {vertical.human_authority.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          {error && <p className="text-sm text-fail">{error}</p>}
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button onClick={() => run(false)} disabled={busy}>
              Record proposal
            </Button>
            <Button
              variant="secondary"
              onClick={() => run(true)}
              disabled={busy || (current.status !== "AWAITING_APPROVAL" && current.status !== "ESCALATED")}
            >
              Human approve (no side effect)
            </Button>
          </div>
          <p className="text-xs text-subtle">
            Prohibited: {vertical.prohibited_actions.join("; ")}
          </p>
        </CardContent>
      </Card>
      <div className="space-y-4">
        {receipt ? (
          <ReceiptCard receipt={receipt} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Receipt</CardTitle>
              <CardDescription>
                Run a scenario to append an evidence-bearing receipt to the local durable ledger.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link
                to="/verify"
                className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
              >
                Open verifier
              </Link>
            </CardContent>
          </Card>
        )}
        <Card>
          <CardHeader>
            <CardTitle>Authority boundary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted">
            <p>Formulas bound: {vertical.formula_bindings.join(", ")}. None grant authority.</p>
            <p>Stage {vertical.stage}. Visibility {vertical.space_visibility}.</p>
            <p>{vertical.public_launch.replaceAll("_", " ")}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
