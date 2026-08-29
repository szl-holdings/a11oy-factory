import { useEffect, useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EffectChip, EvidenceChip, StatusChip } from "@/components/truth-chip";
import { cellOverlay } from "@/lib/admission";
import { investorDemo, type CompiledCell } from "@/lib/compiler";
import { lockedFormulas, profile, verticalById } from "@/lib/data/registry";
import {
  FORGE_TEMPLATES,
  buildForgedScenario,
  clearForged,
  forgeCoverage,
  liveScenarios,
  type ForgeTemplateId,
  upsertForged,
} from "@/lib/forge";
import { runFrontierProgram, releaseGateState, type FrontierRun } from "@/lib/frontier";
import { loadLedger, recordOutcome } from "@/lib/ledger";
import { evaluatePolicy, shadowCompare } from "@/lib/policy";
import type { DecisionReceipt, OutcomeState } from "@/lib/types";

const PROGRAM_IDS = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"] as const;

export function FrontierWorkbench() {
  const [runs, setRuns] = useState<FrontierRun[] | null>(null);
  const [compiled, setCompiled] = useState<CompiledCell[] | null>(null);
  const [active, setActive] = useState<(typeof PROGRAM_IDS)[number]>("N1");
  const [tick, setTick] = useState(0);

  async function refresh() {
    const result = await runFrontierProgram();
    setRuns(result.runs);
    setCompiled(result.compiled);
  }

  useEffect(() => {
    void refresh();
  }, [tick]);

  const current = runs?.find((r) => r.item.id === active);

  return (
    <div className="space-y-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {(runs ?? []).map((run) => (
          <button
            key={run.item.id}
            type="button"
            onClick={() => setActive(run.item.id as (typeof PROGRAM_IDS)[number])}
            className={`rounded-xl border p-4 text-left transition-colors duration-150 ${
              active === run.item.id
                ? "border-accent/50 bg-elevated"
                : "border-border bg-surface hover:border-accent/30"
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="font-mono text-[11px] text-subtle">
                {run.item.id} · {run.item.priority}
              </p>
              <StatusChip value={run.status} />
            </div>
            <p className="mt-2 font-serif text-lg tracking-tight">{run.item.name}</p>
            <p className="mt-2 font-mono text-[11px] text-subtle">
              {run.acceptance_met}/{run.acceptance_total} acceptance
            </p>
          </button>
        ))}
        {!runs && <p className="text-sm text-muted sm:col-span-2">Compiling frontier program…</p>}
      </div>

      {current && (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-mono text-xs text-subtle">{current.item.id}</p>
              <StatusChip value={current.status} />
              <Badge variant={current.item.priority === "P0" ? "fail" : "warn"}>
                {current.item.priority}
              </Badge>
            </div>
            <CardTitle>{current.item.name}</CardTitle>
            <CardDescription>{current.item.novelty}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="max-w-3xl text-pretty text-sm text-muted">{current.item.build}</p>
            <ul className="grid gap-2 sm:grid-cols-2">
              {current.checks.map((check) => (
                <li
                  key={check.id}
                  className="flex items-start gap-3 rounded-lg border border-border bg-elevated p-3"
                >
                  <StatusChip value={check.ok ? "SATISFIED" : "PARTIAL"} />
                  <span className="text-sm text-muted">{check.detail}</span>
                </li>
              ))}
            </ul>
            {active === "N1" && compiled && <CompilerBench compiled={compiled} />}
            {active === "N2" && compiled && <ProtocolBench compiled={compiled} />}
            {active === "N3" && <ShadowBench />}
            {active === "N4" && <LedgerBench onChange={() => setTick((n) => n + 1)} />}
            {active === "N5" && <FormulaBench />}
            {active === "N6" && <ForgeBench onChange={() => setTick((n) => n + 1)} />}
            {active === "N7" && compiled && <ReleaseBench compiled={compiled} />}
            {active === "N8" && <InvestorBench />}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CompilerBench({ compiled }: { compiled: CompiledCell[] }) {
  const [id, setId] = useState(compiled[0]?.vertical_id ?? "lyte-services");
  const cell = compiled.find((c) => c.vertical_id === id);
  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-subtle">
            <tr>
              <th className="py-2 pr-3">Cell</th>
              <th className="py-2 pr-3">Valid</th>
              <th className="py-2">Manifest digest</th>
            </tr>
          </thead>
          <tbody>
            {compiled.map((row) => (
              <tr key={row.vertical_id} className="border-t border-border">
                <td className="py-2 pr-3">
                  <button
                    type="button"
                    className="h-11 font-mono text-xs text-accent underline-offset-4 hover:underline"
                    onClick={() => setId(row.vertical_id)}
                  >
                    {row.vertical_id}
                  </button>
                </td>
                <td className="py-2 pr-3">
                  <StatusChip value={row.valid ? "SATISFIED" : "BLOCKED"} />
                </td>
                <td className="py-2 font-mono text-[11px] text-muted">{row.manifest_digest}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {cell && (
        <pre className="max-h-[360px] overflow-auto rounded-lg border border-border bg-elevated p-4 font-mono text-[11px] leading-relaxed text-muted">
          {JSON.stringify(
            {
              vertical_id: cell.vertical_id,
              manifest_digest: cell.manifest_digest,
              route: cell.contracts.route.routes.map((r) => r.path),
              policy_revision: cell.contracts.policy.policy_revision,
              ui_fields: cell.contracts.ui.component_truth_fields,
            },
            null,
            2,
          )}
        </pre>
      )}
    </div>
  );
}

function ProtocolBench({ compiled }: { compiled: CompiledCell[] }) {
  const fields = compiled[0]?.contracts.ui.component_truth_fields ?? [];
  const sample =
    liveScenarios().find((s) => s.evidence.some((e) => e.class === "UNAVAILABLE")) ??
    liveScenarios()[0];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {fields.map((field) => (
          <Badge key={field} variant="accent">
            {field}
          </Badge>
        ))}
      </div>
      {sample && (
        <div className="rounded-lg border border-border bg-elevated p-4">
          <p className="text-xs uppercase tracking-wide text-subtle">Degraded card example</p>
          <p className="mt-2 font-serif text-xl tracking-tight">{sample.title}</p>
          <p className="mt-1 text-sm text-muted">{sample.summary}</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {sample.evidence.map((item) => (
              <span key={item.evidence_id} className="inline-flex items-center gap-1.5">
                <EvidenceChip value={item.class} />
                <span className="text-xs text-muted">
                  {item.label} · {item.freshness}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ShadowBench() {
  const list = liveScenarios();
  const [id, setId] = useState(list[0]?.scenario_id ?? "");
  const [promotion, setPromotion] = useState<string | null>(null);
  const scenario = list.find((s) => s.scenario_id === id) ?? list[0];
  const vertical = scenario ? verticalById(scenario.vertical_id) : undefined;
  const run = useMemo(() => {
    if (!scenario || !vertical) return null;
    return shadowCompare(vertical, scenario);
  }, [scenario, vertical]);
  const current = scenario && vertical ? evaluatePolicy(vertical, scenario, "LOG_ONLY") : null;

  if (!scenario || !vertical || !run || !current) {
    return <p className="text-sm text-muted">No live scenarios.</p>;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="space-y-4">
        <label className="block">
          <span className="text-xs uppercase tracking-wide text-muted">Scenario</span>
          <select
            className="mt-1 h-11 w-full rounded-lg border border-border bg-elevated px-3 text-sm"
            value={scenario.scenario_id}
            onChange={(e) => {
              setId(e.target.value);
              setPromotion(null);
            }}
          >
            {list.map((item) => (
              <option key={item.scenario_id} value={item.scenario_id}>
                {item.vertical_id} — {item.title}
              </option>
            ))}
          </select>
        </label>
        <p className="text-sm text-muted">{scenario.summary}</p>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs uppercase tracking-wide text-subtle">current</span>
          <EffectChip value={current.effect} />
          <span className="text-xs uppercase tracking-wide text-subtle">candidate</span>
          <EffectChip value={run.candidate.effect} />
          {run.differs ? <Badge variant="warn">differs</Badge> : <Badge>no delta</Badge>}
        </div>
        <Button
          variant="secondary"
          onClick={() =>
            setPromotion(
              "REFUSED. Candidate stays LOG_ONLY. Promotion requires an exact revision, human review, runtime readback, and a rollback receipt. This preview cannot change authority.",
            )
          }
        >
          Promote candidate (will refuse)
        </Button>
        {promotion && <p className="text-sm text-warn">{promotion}</p>}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Current reasons</p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {run.current.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Candidate reasons</p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {run.candidate.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function LedgerBench({ onChange }: { onChange: () => void }) {
  const [entries, setEntries] = useState<DecisionReceipt[]>([]);
  useEffect(() => {
    setEntries(loadLedger().entries.slice().reverse());
  }, []);

  async function setOutcome(id: string, outcome: OutcomeState) {
    const next = await recordOutcome(id, outcome);
    if (next) {
      setEntries(loadLedger().entries.slice().reverse());
      onChange();
    }
  }

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted">
        Ledger is empty. Record a proposal in a vertical theatre, then attach a late outcome here.
        No automatic retraining.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {entries.slice(0, 6).map((entry) => (
        <div key={entry.decision_id} className="rounded-lg border border-border bg-elevated p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-mono text-xs text-subtle">
              {entry.vertical_id} · {entry.decision_id}
            </p>
            <StatusChip value={entry.outcome_state} />
          </div>
          <p className="mt-2 text-sm text-muted">{entry.proposal.summary}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(["MEASURED", "CORRECTED", "REVOKED", "UNAVAILABLE"] as OutcomeState[]).map((state) => (
              <Button
                key={state}
                size="sm"
                variant="secondary"
                onClick={() => void setOutcome(entry.decision_id, state)}
              >
                {state}
              </Button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function FormulaBench() {
  const locked = lockedFormulas();
  const leak = profile.formula_bindings.filter((f) => f.grants_authority !== false);
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat k="Locked-proved" v={String(locked.length)} />
        <Stat k="Catalogue" v={String(profile.formula_bindings.length)} />
        <Stat k="Authority grants" v={String(leak.length)} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-subtle">
            <tr>
              <th className="py-2 pr-3">ID</th>
              <th className="py-2 pr-3">Class</th>
              <th className="py-2 pr-3">Authority</th>
              <th className="py-2">Binding</th>
            </tr>
          </thead>
          <tbody>
            {profile.formula_bindings.map((item) => (
              <tr key={item.formula_id} className="border-t border-border align-top">
                <td className="py-2 pr-3 font-mono">{item.formula_id}</td>
                <td className="py-2 pr-3">
                  <Badge variant={item.proof_class.startsWith("LOCKED") ? "pass" : "warn"}>
                    {item.proof_class}
                  </Badge>
                </td>
                <td className="py-2 pr-3">{String(item.grants_authority)}</td>
                <td className="py-2 text-muted">{item.allowed_runtime_binding}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ForgeBench({ onChange }: { onChange: () => void }) {
  const [coverage, setCoverage] = useState(forgeCoverage());
  const [verticalId, setVerticalId] = useState(
    profile.vertical_cells[0]?.vertical_id ?? "lyte-services",
  );
  const [template, setTemplate] = useState<ForgeTemplateId>("positive");
  const [last, setLast] = useState<string | null>(null);

  function refresh() {
    setCoverage(forgeCoverage());
    onChange();
  }

  function forgeOne() {
    const vertical = verticalById(verticalId);
    if (!vertical) return;
    const scenario = buildForgedScenario(vertical, template);
    upsertForged(scenario);
    setLast(scenario.scenario_id);
    refresh();
  }

  function forgeAll() {
    for (const cell of profile.vertical_cells) {
      for (const t of FORGE_TEMPLATES) {
        upsertForged(buildForgedScenario(cell, t.id));
      }
    }
    setLast("all five templates × seven cells");
    refresh();
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="text-xs uppercase tracking-wide text-muted">Vertical</span>
          <select
            className="mt-1 h-11 w-full rounded-lg border border-border bg-elevated px-3 text-sm"
            value={verticalId}
            onChange={(e) => setVerticalId(e.target.value)}
          >
            {profile.vertical_cells.map((cell) => (
              <option key={cell.vertical_id} value={cell.vertical_id}>
                {cell.display_name.split("—")[0]}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-xs uppercase tracking-wide text-muted">Template</span>
          <select
            className="mt-1 h-11 w-full rounded-lg border border-border bg-elevated px-3 text-sm"
            value={template}
            onChange={(e) => setTemplate(e.target.value as ForgeTemplateId)}
          >
            {FORGE_TEMPLATES.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button onClick={forgeOne}>Forge this fixture</Button>
        <Button variant="secondary" onClick={forgeAll}>
          Fill every cell
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            clearForged();
            setLast("cleared");
            refresh();
          }}
        >
          Clear forged
        </Button>
      </div>
      {last && <p className="text-xs text-subtle">Last write: {last}</p>}
      <p className="text-sm text-muted">
        Coverage {coverage.complete_cells}/{coverage.verticals} cells · seed {coverage.seed_total} ·
        forged {coverage.forged_total}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-subtle">
            <tr>
              <th className="py-2 pr-3">Cell</th>
              {FORGE_TEMPLATES.map((t) => (
                <th key={t.id} className="py-2 pr-3">
                  {t.id}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {coverage.rows.map((row) => (
              <tr key={row.vertical_id} className="border-t border-border">
                <td className="py-2 pr-3 font-mono text-xs">{row.vertical_id}</td>
                {row.templates.map((t) => (
                  <td key={t.id} className="py-2 pr-3">
                    <StatusChip value={t.present ? "SATISFIED" : "EMPTY"} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReleaseBench({ compiled }: { compiled: CompiledCell[] }) {
  const [id, setId] = useState("lyte-services");
  const cell = compiled.find((c) => c.vertical_id === id);
  const vertical = verticalById(id);
  if (!cell || !vertical) return null;
  const gates = releaseGateState(cell, vertical);
  const overlay = cellOverlay(id);
  return (
    <div className="space-y-4">
      <label className="block max-w-md">
        <span className="text-xs uppercase tracking-wide text-muted">Cell</span>
        <select
          className="mt-1 h-11 w-full rounded-lg border border-border bg-elevated px-3 text-sm"
          value={id}
          onChange={(e) => setId(e.target.value)}
        >
          {compiled.map((c) => (
            <option key={c.vertical_id} value={c.vertical_id}>
              {c.vertical_id}
            </option>
          ))}
        </select>
      </label>
      <p className="text-sm text-muted">
        Target visibility {overlay.space_visibility}. {overlay.public_launch}. One writer, one image,
        signed manifest {cell.manifest_digest.slice(0, 16)}…
      </p>
      <ul className="space-y-2">
        {gates.map((gate) => (
          <li
            key={gate.gate}
            className="flex flex-col gap-1 rounded-lg border border-border bg-elevated p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="text-sm">{gate.gate}</p>
              <p className="text-xs text-subtle">{gate.note}</p>
            </div>
            <StatusChip value={gate.state} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function InvestorBench() {
  const lyte = verticalById("lyte-services")!;
  const demo = investorDemo(lyte);
  return (
    <div className="space-y-4">
      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {demo.three_minute_sequence.map((step) => (
          <li key={step.step} className="rounded-lg border border-border bg-elevated p-3">
            <p className="font-mono text-[11px] text-subtle">{String(step.step).padStart(2, "0")}</p>
            <p className="mt-1 text-sm">{step.show}</p>
          </li>
        ))}
      </ol>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button asChild>
          <Link to="/investor">Run investor theatre</Link>
        </Button>
        <Button variant="secondary" asChild>
          <Link to="/verticals/$id" params={{ id: "lyte-services" }}>
            Lyte cell
          </Link>
        </Button>
      </div>
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
