import type { DecisionReceipt, OutcomeState, Scenario, VerticalCell } from "@/lib/types";
import { canonicalJson, digestText } from "@/lib/hash";
import {
  POLICY_REVISION,
  RUNTIME_REVISION,
  SOURCE_REVISION,
} from "@/lib/data/registry";
import { evaluatePolicy, shadowCompare, type PolicyResult } from "@/lib/policy";

const STORAGE_KEY = "a11oy.ledger.v1";
const GENESIS = "0".repeat(64);

export interface LedgerState {
  schema: "szl.outcome-feedback-ledger/v1";
  genesis: string;
  entries: DecisionReceipt[];
}

function emptyLedger(): LedgerState {
  return { schema: "szl.outcome-feedback-ledger/v1", genesis: GENESIS, entries: [] };
}

export function loadLedger(): LedgerState {
  if (typeof window === "undefined") return emptyLedger();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyLedger();
    const parsed = JSON.parse(raw) as LedgerState;
    if (!Array.isArray(parsed.entries)) return emptyLedger();
    return parsed;
  } catch {
    return emptyLedger();
  }
}

export function saveLedger(ledger: LedgerState): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ledger));
}

export function headHash(ledger: LedgerState): string {
  const last = ledger.entries[ledger.entries.length - 1];
  return last?.hash ?? ledger.genesis;
}

function receiptWithoutHash(
  vertical: VerticalCell,
  scenario: Scenario,
  result: PolicyResult,
  actor: string,
  approved: boolean,
  status: DecisionReceipt["decision"]["status"],
  manifestDigest: string,
  prev: string,
  shadow?: DecisionReceipt["policy"]["shadow"],
): Omit<DecisionReceipt, "hash"> {
  const now = new Date().toISOString();
  return {
    schema: "szl.vertical-decision-receipt/v1",
    vertical_id: vertical.vertical_id,
    decision_id: `dec_${scenario.scenario_id}_${Date.now().toString(36)}`,
    tenant_id: "preview.local",
    scenario_id: scenario.scenario_id,
    source_revision: SOURCE_REVISION,
    runtime_revision: RUNTIME_REVISION,
    manifest_digest: manifestDigest,
    prev_hash: prev,
    evidence: scenario.evidence,
    policy: {
      mode: "LOG_ONLY",
      revision: POLICY_REVISION,
      effect: result.effect,
      reasons: result.reasons,
      formula_grants_authority: false,
      shadow,
    },
    authority: {
      required: vertical.human_authority,
      actor,
      approved,
    },
    proposal: {
      action: String(scenario.facts.requested_action ?? "recommend"),
      summary: scenario.summary,
      cannot_grant_authority: true,
    },
    decision: {
      status,
      rationale: result.reasons.join("; "),
    },
    outcome_state: "PENDING",
    created_at: now,
    limitations: [
      "Factory preview — not a production certification.",
      "Formula bindings never grant authority.",
      vertical.vertical_id === "killinchu"
        ? "SIMULATED proposal-only; no physical effector."
        : `Public launch: ${vertical.public_launch}`,
    ],
  };
}

export async function appendDecision(opts: {
  vertical: VerticalCell;
  scenario: Scenario;
  actor: string;
  approve?: boolean;
  manifestDigest: string;
  includeShadow?: boolean;
}): Promise<DecisionReceipt> {
  const ledger = loadLedger();
  const result = evaluatePolicy(opts.vertical, opts.scenario, "LOG_ONLY");
  let status = result.status;
  let approved = false;
  if (opts.approve && result.status === "AWAITING_APPROVAL") {
    status = "APPROVED";
    approved = true;
  }
  if (opts.approve && result.status === "ESCALATED") {
    status = "APPROVED";
    approved = true;
  }
  const shadowRun = opts.includeShadow
    ? shadowCompare(opts.vertical, opts.scenario)
    : null;
  const prev = headHash(ledger);
  const unsigned = receiptWithoutHash(
    opts.vertical,
    opts.scenario,
    result,
    opts.actor,
    approved,
    status,
    opts.manifestDigest,
    prev,
    shadowRun
      ? {
          candidate_effect: shadowRun.candidate.effect,
          candidate_reasons: shadowRun.candidate.reasons,
          differs: shadowRun.differs,
        }
      : undefined,
  );
  const hash = await digestText(canonicalJson(unsigned));
  const receipt: DecisionReceipt = { ...unsigned, hash };
  ledger.entries.push(receipt);
  saveLedger(ledger);
  return receipt;
}

export async function recordOutcome(
  decisionId: string,
  outcome: OutcomeState,
): Promise<DecisionReceipt | null> {
  const ledger = loadLedger();
  const index = ledger.entries.findIndex((e) => e.decision_id === decisionId);
  if (index < 0) return null;
  const next = { ...ledger.entries[index], outcome_state: outcome };
  ledger.entries[index] = next;
  saveLedger(ledger);
  return next;
}

export interface VerifyResult {
  ok: boolean;
  findings: string[];
  inLedger: boolean;
  chainOk: boolean;
}

export async function verifyReceipt(receipt: DecisionReceipt): Promise<VerifyResult> {
  const findings: string[] = [];
  if (receipt.schema !== "szl.vertical-decision-receipt/v1") {
    findings.push("unknown receipt schema");
  }
  if (receipt.policy.formula_grants_authority !== false) {
    findings.push("formula must not grant authority");
  }
  const { hash, ...rest } = receipt;
  const expected = await digestText(canonicalJson(rest));
  if (expected !== hash) findings.push("hash does not match canonical body");

  const ledger = loadLedger();
  const inLedger = ledger.entries.some((e) => e.hash === receipt.hash);
  let chainOk = true;
  let prev = ledger.genesis;
  for (const entry of ledger.entries) {
    if (entry.prev_hash !== prev) {
      chainOk = false;
      findings.push(`chain break at ${entry.decision_id}`);
      break;
    }
    prev = entry.hash;
  }
  if (!inLedger) findings.push("receipt is not in the local durable ledger (self-contained check only)");

  return {
    ok: findings.filter((f) => !f.startsWith("receipt is not")).length === 0,
    findings,
    inLedger,
    chainOk,
  };
}

export function exportLedgerBundle(): string {
  return JSON.stringify(loadLedger(), null, 2);
}

export function clearLedger(): void {
  saveLedger(emptyLedger());
}
