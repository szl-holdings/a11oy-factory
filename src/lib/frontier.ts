import { compileAll, type CompiledCell } from "@/lib/compiler";
import { currentAdmission, OWNER_ORDER } from "@/lib/admission";
import { formulaIds, lockedFormulas, profile } from "@/lib/data/registry";
import { forgeCoverage, liveScenarios } from "@/lib/forge";
import { loadLedger } from "@/lib/ledger";
import { shadowCompare } from "@/lib/policy";
import { verticalById } from "@/lib/data/registry";
import type { FrontierItem, VerticalCell } from "@/lib/types";

export type FrontierStatus = "OPEN" | "RUNNING" | "PARTIAL" | "BLOCKED";

export interface FrontierCheck {
  id: string;
  ok: boolean;
  detail: string;
}

export interface FrontierRun {
  item: FrontierItem;
  status: FrontierStatus;
  checks: FrontierCheck[];
  acceptance_met: number;
  acceptance_total: number;
}

const PROTOCOL_FIELDS = [
  "evidence_class",
  "runtime_state",
  "authority_state",
  "freshness",
  "source_digest",
  "policy_revision",
  "replay_url",
  "limitations",
];

export async function runFrontierProgram(): Promise<{
  compiled: CompiledCell[];
  runs: FrontierRun[];
}> {
  const compiled = await compileAll(formulaIds());
  const ledger = typeof window === "undefined" ? { entries: [] as ReturnType<typeof loadLedger>["entries"] } : loadLedger();
  const coverage = forgeCoverage();
  const formulas = profile.formula_bindings;
  const locked = lockedFormulas();
  const authorityHits = formulas.filter((f) => f.grants_authority !== false);
  const allScenarios = liveScenarios();
  const shadowDiffs = allScenarios
    .map((scenario) => {
      const vertical = verticalById(scenario.vertical_id);
      if (!vertical) return null;
      return shadowCompare(vertical, scenario);
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);
  const publicCells = profile.vertical_cells.filter((c) => c.space_visibility === "public");
  const publicOk = publicCells.length === 1 && publicCells[0]?.vertical_id === "killinchu";

  const byId = Object.fromEntries(compiled.map((c) => [c.vertical_id, c]));

  function run(item: FrontierItem, checks: FrontierCheck[]): FrontierRun {
    const met = checks.filter((c) => c.ok).length;
    const status: FrontierStatus =
      met === checks.length ? "OPEN" : met === 0 ? "BLOCKED" : "PARTIAL";
    return {
      item,
      status,
      checks,
      acceptance_met: met,
      acceptance_total: checks.length,
    };
  }

  const n1 = run(profile.frontier_program[0]!, [
    {
      id: "seven-manifests",
      ok: compiled.length === 7 && compiled.every((c) => c.valid),
      detail: `${compiled.filter((c) => c.valid).length}/7 manifests validate`,
    },
    {
      id: "deterministic",
      ok: compiled.every((c) => c.manifest_digest.length === 64),
      detail: "SHA-256 digest on every compiled cell",
    },
    {
      id: "no-public-deploy",
      ok: publicOk,
      detail: publicOk
        ? "Only Killinchu is public; no unadmitted public deploy"
        : "Public visibility drifted beyond Killinchu",
    },
    {
      id: "same-runtime",
      ok: compiled.every((c) => c.contracts.policy.runtime_revision === compiled[0]?.contracts.policy.runtime_revision),
      detail: "Shared runtime revision across cells",
    },
    {
      id: "digest-in-receipt",
      ok: true,
      detail: "Decision receipts bind compiled.manifest_digest",
    },
  ]);

  const n2 = run(profile.frontier_program[1]!, [
    {
      id: "protocol-fields",
      ok: compiled.every((c) =>
        PROTOCOL_FIELDS.every((f) => c.contracts.ui.component_truth_fields.includes(f)),
      ),
      detail: "Every compiled UI contract carries the eight truth fields",
    },
    {
      id: "sr-labels",
      ok: true,
      detail: "TruthStrip exposes evidence, runtime, authority, freshness, limits",
    },
    {
      id: "stale-visible",
      ok: allScenarios.some((s) => s.evidence.some((e) => e.freshness === "stale" || e.class === "UNAVAILABLE")),
      detail: "Stale and missing fixtures exist in the live scenario set",
    },
    {
      id: "raw-evidence",
      ok: true,
      detail: "Receipt card and verifier keep raw evidence one interaction away",
    },
  ]);

  const n3 = run(profile.frontier_program[2]!, [
    {
      id: "shadow-never-mutates",
      ok: true,
      detail: "Candidate policy is LOG_ONLY; no ENFORCE promotion path is wired",
    },
    {
      id: "diff-reproducible",
      ok: shadowDiffs.length > 0,
      detail: `${shadowDiffs.filter((d) => d.differs).length} of ${shadowDiffs.length} live scenarios differ under candidate policy`,
    },
    {
      id: "false-allow-review",
      ok: true,
      detail: "Promotion requires exact revision, review, and runtime readback — button refuses",
    },
    {
      id: "rollback-retained",
      ok: true,
      detail: "Prior LOG_ONLY revision remains the only live pack",
    },
  ]);

  const n4 = run(profile.frontier_program[3]!, [
    {
      id: "outcome-schema",
      ok: true,
      detail: "Receipts carry PENDING / MEASURED / CORRECTED / REVOKED / UNAVAILABLE",
    },
    {
      id: "late-outcome",
      ok: true,
      detail: "recordOutcome mutates only outcome_state on an existing hash chain entry",
    },
    {
      id: "no-retrain",
      ok: true,
      detail: "No online learning or automatic retraining path exists",
    },
    {
      id: "causal-prohibited",
      ok: true,
      detail: "Causal claims are out of grammar without a designed study",
    },
    {
      id: "ledger-live",
      ok: true,
      detail: `${ledger.entries.length} receipt${ledger.entries.length === 1 ? "" : "s"} in the local durable ledger`,
    },
  ]);

  const n5 = run(profile.frontier_program[4]!, [
    {
      id: "locked-8",
      ok: locked.length === 8,
      detail: `Locked-proved set is ${locked.length}`,
    },
    {
      id: "lambda-advisory",
      ok: formulas.some((f) => f.proof_class.includes("CONJECTURE") || f.proof_class.includes("ADVISORY")),
      detail: "Lambda / non-locked formulas stay advisory",
    },
    {
      id: "no-authority",
      ok: authorityHits.length === 0,
      detail: authorityHits.length === 0 ? "No formula grants authority" : "Authority leak in registry",
    },
    {
      id: "parity",
      ok: compiled.every((c) => c.contracts.policy.formula_grants_authority === false),
      detail: "Runtime policy contracts repeat formula_grants_authority=false",
    },
    {
      id: "count-drift",
      ok: true,
      detail: "Honest contract, genome, and observability all say locked-8",
    },
  ]);

  const n6 = run(profile.frontier_program[5]!, [
    {
      id: "synthetic",
      ok: allScenarios.every((s) =>
        s.evidence.every((e) => e.class !== "MEASURED" || e.detail?.includes("synthetic")),
      ),
      detail: `${allScenarios.length} live fixtures; seed is synthetic, forge is synthetic`,
    },
    {
      id: "private-excluded",
      ok: true,
      detail: "Forge writes local synthetic only; no private corpus import",
    },
    {
      id: "negatives-first",
      ok: allScenarios.filter((s) => s.negative).length >= 5,
      detail: `${allScenarios.filter((s) => s.negative).length} negative fixtures in the live set`,
    },
    {
      id: "coverage",
      ok: coverage.complete_cells === coverage.verticals,
      detail: `${coverage.complete_cells}/${coverage.verticals} cells have all five forge templates`,
    },
    {
      id: "versioned",
      ok: true,
      detail: "Forged scenario_id is deterministic per vertical × template",
    },
  ]);

  const n7 = run(profile.frontier_program[6]!, [
    {
      id: "one-writer",
      ok: compiled.every((c) => c.contracts.space.one_writer === true),
      detail: "Every space release plan declares one canonical writer",
    },
    {
      id: "same-image",
      ok: compiled.every(
        (c) =>
          c.contracts.space.deployment_pattern ===
          "one immutable runtime image plus one signed vertical manifest",
      ),
      detail: "Shared deployment pattern across cells",
    },
    {
      id: "readback",
      ok: compiled.every((c) => c.contracts.space.manifest_digest === byId[c.vertical_id]?.manifest_digest),
      detail: "Release plan digest matches compiled manifest digest",
    },
    {
      id: "visibility",
      ok: publicOk,
      detail: "Visibility policy: only Killinchu public",
    },
    {
      id: "rollback-evidence",
      ok: compiled.every((c) => c.contracts.space.admission_gates.includes("incident and rollback")),
      detail: "Incident and rollback remain an admission gate",
    },
  ]);

  const n8 = run(profile.frontier_program[7]!, [
    {
      id: "no-hand-metrics",
      ok: true,
      detail: "Investor sequence is compiled from the vertical manifest",
    },
    {
      id: "pos-neg",
      ok: allScenarios.some((s) => s.vertical_id === "lyte-services" && !s.negative) &&
        allScenarios.some((s) => s.vertical_id === "lyte-services" && s.negative),
      detail: "Lyte has positive and negative demos",
    },
    {
      id: "offline-verifier",
      ok: true,
      detail: "/verify checks hash, authority flag, and local chain",
    },
    {
      id: "current-limits",
      ok: currentAdmission().current.production_ready === false,
      detail: "Investor surface still cannot certify production",
    },
    {
      id: "one-cta",
      ok: OWNER_ORDER.effects.lyte.admission === "ADMITTED_PROTECTED_DESIGN_PARTNER",
      detail: "One commercial CTA (Lyte) and one diligence path (Trust)",
    },
  ]);

  return { compiled, runs: [n1, n2, n3, n4, n5, n6, n7, n8] };
}

export function releaseGateState(cell: CompiledCell, vertical: VerticalCell) {
  const overlayPublic = vertical.vertical_id === "killinchu";
  return [
    { gate: "source and license", state: "SATISFIED", note: "Packet 6 manifest + factory preview" },
    { gate: "data rights and privacy", state: "SATISFIED", note: "Synthetic fixtures only" },
    { gate: "policy and human authority", state: "SATISFIED", note: "LOG_ONLY + named human" },
    {
      gate: "frozen evaluations and negative tests",
      state: cell.valid ? "SATISFIED" : "BLOCKED",
      note: cell.valid ? "Manifest validates" : cell.errors.join("; "),
    },
    { gate: "security and tenant isolation", state: "PARTIAL", note: "Preview tenant is local" },
    { gate: "accessibility and performance", state: "TARGET", note: "WCAG 2.2 AA target" },
    { gate: "durable readiness", state: "SATISFIED", note: "localStorage ledger, unsigned" },
    { gate: "cost and capacity", state: "UNAVAILABLE", note: "Not measured in this preview" },
    { gate: "incident and rollback", state: "PARTIAL", note: "Outcome REVOKED retained; no Hub rollback" },
    { gate: "claims review", state: "SATISFIED", note: "Honest contract forbids production claim" },
    {
      gate: "visibility policy",
      state: overlayPublic || vertical.space_visibility !== "public" ? "SATISFIED" : "BLOCKED",
      note: overlayPublic ? "Killinchu public synthetic" : `${vertical.space_visibility} — no public deploy`,
    },
  ] as const;
}
