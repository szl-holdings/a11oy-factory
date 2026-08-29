import type {
  DecisionStatus,
  PolicyEffect,
  PolicyMode,
  Scenario,
  VerticalCell,
} from "@/lib/types";

export interface PolicyResult {
  effect: PolicyEffect;
  status: DecisionStatus;
  reasons: string[];
  requiresHuman: boolean;
  prohibitedHit: string | null;
  evidenceProblems: string[];
}

function fact(scenario: Scenario, key: string): string | number | boolean | undefined {
  return scenario.facts[key];
}

function evidenceProblems(scenario: Scenario): string[] {
  const problems: string[] = [];
  if (scenario.evidence.length === 0) problems.push("no evidence attached");
  for (const item of scenario.evidence) {
    if (item.class === "UNAVAILABLE") problems.push(`${item.label} unavailable`);
    if (item.freshness === "stale") problems.push(`${item.label} is stale`);
  }
  return problems;
}

function lyteRules(scenario: Scenario, reasons: string[]): PolicyEffect {
  if (fact(scenario, "discovery_complete") !== true) {
    reasons.push("missing discovery blocks estimate");
    return "DENY";
  }
  const margin = Number(fact(scenario, "gross_margin_pct") ?? 0);
  const floor = Number(fact(scenario, "margin_floor_pct") ?? 22);
  if (margin < floor) {
    reasons.push(`gross margin ${margin}% is below policy floor ${floor}%`);
    return "ESCALATE";
  }
  if (fact(scenario, "resource_conflict") === true) {
    reasons.push("resource conflict blocks commitment");
    return "DENY";
  }
  if (fact(scenario, "scope_drift") === true) {
    reasons.push("scope drift opens a proposed change order; it cannot be sent");
    return "ESCALATE";
  }
  reasons.push("scope, margin, and capacity satisfy current LOG_ONLY policy");
  return "ALLOW_WITH_APPROVAL";
}

function aegisRules(scenario: Scenario, reasons: string[]): PolicyEffect {
  if (fact(scenario, "identity_present") !== true) {
    reasons.push("identity missing blocks action");
    return "DENY";
  }
  if (fact(scenario, "tenant_match") !== true) {
    reasons.push("customer boundary mismatch denies");
    return "DENY";
  }
  if (fact(scenario, "evidence_fresh") !== true) {
    reasons.push("evidence stale escalates");
    return "ESCALATE";
  }
  if (fact(scenario, "dangerous_command") === true) {
    reasons.push("dangerous command requires explicit approval");
    return "ESCALATE";
  }
  reasons.push("attack-path context is complete enough to propose remediation");
  return "ALLOW_WITH_APPROVAL";
}

function vesselsRules(scenario: Scenario, reasons: string[]): PolicyEffect {
  if (fact(scenario, "license_present") !== true) {
    reasons.push("license absent blocks data");
    return "DENY";
  }
  if (fact(scenario, "ais_conflict") === true) {
    reasons.push("AIS conflict stays unresolved");
    return "ESCALATE";
  }
  if (fact(scenario, "ownership_gap") === true) {
    reasons.push("ownership gap escalates");
    return "ESCALATE";
  }
  if (fact(scenario, "sanctions_match") === true) {
    reasons.push("sanctions match requires analyst");
    return "ESCALATE";
  }
  reasons.push("voyage screening may be recommended; no commercial execution from this cell");
  return "ALLOW_WITH_APPROVAL";
}

function terraRules(scenario: Scenario, reasons: string[]): PolicyEffect {
  if (fact(scenario, "parcel_identity_ok") !== true) {
    reasons.push("parcel identity conflict blocks");
    return "DENY";
  }
  if (fact(scenario, "amendment_complete") !== true) {
    reasons.push("missing amendment lowers completeness");
    return "ESCALATE";
  }
  if (fact(scenario, "ownership_certain") !== true) {
    reasons.push("ownership uncertainty escalates");
    return "ESCALATE";
  }
  reasons.push("committee memo may be drafted; no transaction execution");
  return "ALLOW_WITH_APPROVAL";
}

function counselRules(scenario: Scenario, reasons: string[]): PolicyEffect {
  if (fact(scenario, "jurisdiction") === "" || !fact(scenario, "jurisdiction")) {
    reasons.push("jurisdiction absent blocks answer");
    return "DENY";
  }
  if (fact(scenario, "authority_current") !== true) {
    reasons.push("authority not current escalates");
    return "ESCALATE";
  }
  if (fact(scenario, "cited") !== true) {
    reasons.push("uncited proposition rejected");
    return "DENY";
  }
  reasons.push("cited draft may be requested for attorney review; no filing");
  return "ALLOW_WITH_APPROVAL";
}

function insuranceRules(scenario: Scenario, reasons: string[]): PolicyEffect {
  if (fact(scenario, "consent") !== true) {
    reasons.push("missing consent blocks");
    return "DENY";
  }
  if (fact(scenario, "protected_attribute_used") === true) {
    reasons.push("protected attribute excluded");
    return "DENY";
  }
  if (fact(scenario, "confidence") === "low") {
    reasons.push("low confidence abstains");
    return "ABSTAIN";
  }
  reasons.push("consent-bound triage may be recommended; no automatic binding or denial");
  return "ALLOW_WITH_APPROVAL";
}

function killinchuRules(scenario: Scenario, reasons: string[]): PolicyEffect {
  if (fact(scenario, "provenance") !== true) {
    reasons.push("missing provenance denies");
    return "DENY";
  }
  if (fact(scenario, "geofence_ok") !== true) {
    reasons.push("geofence conflict denies");
    return "DENY";
  }
  if (fact(scenario, "policy_present") !== true) {
    reasons.push("policy absent blocks");
    return "DENY";
  }
  if (fact(scenario, "requests_effector") === true) {
    reasons.push("physical effector integration is prohibited in the public cell");
    return "DENY";
  }
  reasons.push("synthetic observation may be recommended or escalated; human decision is mandatory");
  return "ESCALATE";
}

const RULES: Record<string, (s: Scenario, reasons: string[]) => PolicyEffect> = {
  "lyte-services": lyteRules,
  "aegis-assurance": aegisRules,
  "vessels-assurance": vesselsRules,
  "terra-assurance": terraRules,
  "counsel-assurance": counselRules,
  "insurance-assurance": insuranceRules,
  killinchu: killinchuRules,
};

function effectToStatus(effect: PolicyEffect): DecisionStatus {
  switch (effect) {
    case "DENY":
      return "DENIED";
    case "ABSTAIN":
      return "ABSTAINED";
    case "ESCALATE":
      return "ESCALATED";
    case "PROPOSE":
      return "PROPOSED";
    case "ALLOW_WITH_APPROVAL":
      return "AWAITING_APPROVAL";
  }
}

export function evaluatePolicy(
  vertical: VerticalCell,
  scenario: Scenario,
  _mode: PolicyMode = "LOG_ONLY",
): PolicyResult {
  const reasons: string[] = [];
  const problems = evidenceProblems(scenario);
  const requested = String(fact(scenario, "requested_action") ?? "recommend");
  const prohibitedHit =
    vertical.prohibited_actions.find((item) =>
      requested.toLowerCase().includes(item.toLowerCase().slice(0, 18)),
    ) ?? (fact(scenario, "requests_effector") === true ? "physical effector integration in public Space" : null);

  if (prohibitedHit) {
    reasons.push(`prohibited action: ${prohibitedHit}`);
    return {
      effect: "DENY",
      status: "DENIED",
      reasons,
      requiresHuman: true,
      prohibitedHit,
      evidenceProblems: problems,
    };
  }

  if (problems.some((p) => p.includes("unavailable") || p.includes("no evidence"))) {
    reasons.push(...problems);
    reasons.push("fail-closed: missing evidence cannot authorize");
    return {
      effect: "DENY",
      status: "DENIED",
      reasons,
      requiresHuman: true,
      prohibitedHit: null,
      evidenceProblems: problems,
    };
  }

  const rule = RULES[vertical.vertical_id];
  const effect = rule ? rule(scenario, reasons) : "DENY";
  if (!rule) reasons.push("no vertical rulepack; default DENY");
  if (problems.length && effect !== "DENY") {
    reasons.push(...problems.map((p) => `degraded: ${p}`));
  }

  return {
    effect,
    status: effectToStatus(effect),
    reasons,
    requiresHuman: true,
    prohibitedHit: null,
    evidenceProblems: problems,
  };
}

export function shadowCompare(
  vertical: VerticalCell,
  scenario: Scenario,
): { current: PolicyResult; candidate: PolicyResult; differs: boolean } {
  const current = evaluatePolicy(vertical, scenario, "LOG_ONLY");
  // Candidate tightens margin floor / confidence — still LOG_ONLY, never mutates.
  const candidateScenario: Scenario = {
    ...scenario,
    facts: {
      ...scenario.facts,
      margin_floor_pct: Number(scenario.facts.margin_floor_pct ?? 22) + 3,
      confidence:
        scenario.facts.confidence === "medium" ? "low" : scenario.facts.confidence,
    },
  };
  const candidate = evaluatePolicy(vertical, candidateScenario, "LOG_ONLY");
  return {
    current,
    candidate,
    differs: current.effect !== candidate.effect,
  };
}
