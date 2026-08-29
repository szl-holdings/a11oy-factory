import type { EvidenceClass, Scenario, VerticalCell } from "@/lib/types";
import { profile } from "@/lib/data/registry";
import { scenarios } from "@/lib/scenarios";

const STORAGE_KEY = "a11oy.forge.v1";

export const FORGE_TEMPLATES = [
  {
    id: "positive",
    name: "Positive path",
    novelty: "Rights-cleared happy path with current evidence.",
  },
  {
    id: "stale-evidence",
    name: "Stale evidence",
    novelty: "Same facts, degraded freshness — must be visible on the card.",
  },
  {
    id: "missing-evidence",
    name: "Missing evidence",
    novelty: "Fail-closed. UNAVAILABLE evidence cannot authorize.",
  },
  {
    id: "prohibited",
    name: "Prohibited action",
    novelty: "Request that hits the cell's prohibited list.",
  },
  {
    id: "policy-conflict",
    name: "Policy conflict",
    novelty: "In-policy facts that force escalate or deny.",
  },
] as const;

export type ForgeTemplateId = (typeof FORGE_TEMPLATES)[number]["id"];

interface ForgeStore {
  schema: "szl.vertical-scenario-forge/v1";
  entries: Scenario[];
}

function emptyStore(): ForgeStore {
  return { schema: "szl.vertical-scenario-forge/v1", entries: [] };
}

export function loadForged(): Scenario[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ForgeStore;
    return Array.isArray(parsed.entries) ? parsed.entries : [];
  } catch {
    return [];
  }
}

function saveForged(entries: Scenario[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ schema: "szl.vertical-scenario-forge/v1", entries } satisfies ForgeStore),
  );
}

const POSITIVE_FACTS: Record<string, Scenario["facts"]> = {
  "lyte-services": {
    discovery_complete: true,
    gross_margin_pct: 28,
    margin_floor_pct: 22,
    resource_conflict: false,
    scope_drift: false,
    requested_action: "recommend SOW",
  },
  "aegis-assurance": {
    identity_present: true,
    tenant_match: true,
    evidence_fresh: true,
    dangerous_command: false,
    requested_action: "draft remediation",
  },
  "vessels-assurance": {
    license_present: true,
    ais_conflict: false,
    ownership_gap: false,
    sanctions_match: false,
    requested_action: "recommend screening",
  },
  "terra-assurance": {
    parcel_identity_ok: true,
    amendment_complete: true,
    ownership_certain: true,
    requested_action: "draft memo",
  },
  "counsel-assurance": {
    jurisdiction: "NY",
    authority_current: true,
    cited: true,
    requested_action: "draft",
  },
  "insurance-assurance": {
    consent: true,
    protected_attribute_used: false,
    confidence: "high",
    requested_action: "recommend handoff",
  },
  killinchu: {
    provenance: true,
    geofence_ok: true,
    policy_present: true,
    requests_effector: false,
    requested_action: "recommend",
  },
};

const CONFLICT_FACTS: Record<string, Scenario["facts"]> = {
  "lyte-services": {
    discovery_complete: true,
    gross_margin_pct: 31,
    margin_floor_pct: 22,
    resource_conflict: true,
    requested_action: "recommend SOW",
  },
  "aegis-assurance": {
    identity_present: true,
    tenant_match: false,
    evidence_fresh: true,
    requested_action: "draft remediation",
  },
  "vessels-assurance": {
    license_present: true,
    ais_conflict: false,
    ownership_gap: false,
    sanctions_match: true,
    requested_action: "recommend screening",
  },
  "terra-assurance": {
    parcel_identity_ok: true,
    amendment_complete: true,
    ownership_certain: false,
    requested_action: "draft memo",
  },
  "counsel-assurance": {
    jurisdiction: "NY",
    authority_current: false,
    cited: true,
    requested_action: "draft",
  },
  "insurance-assurance": {
    consent: true,
    protected_attribute_used: true,
    confidence: "high",
    requested_action: "recommend handoff",
  },
  killinchu: {
    provenance: true,
    geofence_ok: false,
    policy_present: true,
    requests_effector: false,
    requested_action: "recommend",
  },
};

function evidence(
  id: string,
  cls: EvidenceClass,
  freshness: string,
  label: string,
): Scenario["evidence"][number] {
  return {
    evidence_id: id,
    class: cls,
    digest: `${id}-forge`,
    freshness,
    label,
    detail: "Forge-generated synthetic fixture. Rights-cleared. Not production data.",
  };
}

export function buildForgedScenario(
  vertical: VerticalCell,
  template: ForgeTemplateId,
): Scenario {
  const vid = vertical.vertical_id;
  const scenarioId = `forge-${vid}-${template}`;
  const prohibited = vertical.prohibited_actions[0] ?? "unauthorized execution";
  const baseLabel = `${vertical.display_name.split("—")[0].trim()} fixture`;

  if (template === "missing-evidence") {
    return {
      scenario_id: scenarioId,
      vertical_id: vid,
      title: `Forged — missing evidence`,
      summary: `No current evidence for ${vertical.display_name.split("—")[0].trim()}. Fail closed.`,
      workflow: vertical.core_workflows[0] ?? "governed decision",
      expected: "DENIED",
      negative: true,
      evidence: [evidence("ev-missing", "UNAVAILABLE", "missing", baseLabel)],
      facts: {
        ...(POSITIVE_FACTS[vid] ?? {}),
        requested_action: "recommend",
      },
    };
  }

  if (template === "stale-evidence") {
    return {
      scenario_id: scenarioId,
      vertical_id: vid,
      title: `Forged — stale evidence`,
      summary: `Facts may be in policy; evidence is stale and must degrade the card.`,
      workflow: vertical.core_workflows[0] ?? "governed decision",
      expected: "AWAITING_APPROVAL",
      negative: true,
      evidence: [evidence("ev-stale", "SIMULATED", "stale", baseLabel)],
      facts: { ...(POSITIVE_FACTS[vid] ?? { requested_action: "recommend" }) },
    };
  }

  if (template === "prohibited") {
    return {
      scenario_id: scenarioId,
      vertical_id: vid,
      title: `Forged — prohibited action`,
      summary: `Request hits prohibited action: ${prohibited}`,
      workflow: vertical.core_workflows[0] ?? "governed decision",
      expected: "DENIED",
      negative: true,
      evidence: [evidence("ev-prohibited", "SIMULATED", "current", baseLabel)],
      facts: {
        ...(POSITIVE_FACTS[vid] ?? {}),
        requested_action: prohibited,
        requests_effector: vid === "killinchu",
      },
    };
  }

  if (template === "policy-conflict") {
    return {
      scenario_id: scenarioId,
      vertical_id: vid,
      title: `Forged — policy conflict`,
      summary: `In-grammar facts that the cell must escalate or deny.`,
      workflow: vertical.core_workflows[0] ?? "governed decision",
      expected: "DENIED",
      negative: true,
      evidence: [evidence("ev-conflict", "SIMULATED", "current", baseLabel)],
      facts: { ...(CONFLICT_FACTS[vid] ?? { requested_action: "recommend" }) },
    };
  }

  return {
    scenario_id: scenarioId,
    vertical_id: vid,
    title: `Forged — positive path`,
    summary: `Synthetic positive fixture for ${vertical.display_name.split("—")[0].trim()}. Proposal only.`,
    workflow: vertical.core_workflows[0] ?? "governed decision",
    expected: vid === "killinchu" ? "ESCALATED" : "AWAITING_APPROVAL",
    evidence: [evidence("ev-positive", "SIMULATED", "current", baseLabel)],
    facts: { ...(POSITIVE_FACTS[vid] ?? { requested_action: "recommend" }) },
  };
}

export function upsertForged(scenario: Scenario): Scenario[] {
  const next = loadForged().filter((item) => item.scenario_id !== scenario.scenario_id);
  next.push(scenario);
  saveForged(next);
  return next;
}

export function clearForged(): void {
  saveForged([]);
}

export function liveScenarios(): Scenario[] {
  return [...scenarios, ...loadForged()];
}

export function liveScenariosFor(verticalId: string): Scenario[] {
  return liveScenarios().filter((item) => item.vertical_id === verticalId);
}

export function forgeCoverage() {
  const forged = loadForged();
  const cells = profile.vertical_cells;
  const rows = cells.map((cell) => {
    const seed = scenarios.filter((s) => s.vertical_id === cell.vertical_id);
    const made = forged.filter((s) => s.vertical_id === cell.vertical_id);
    const templates = FORGE_TEMPLATES.map((t) => ({
      id: t.id,
      present: made.some((s) => s.scenario_id === `forge-${cell.vertical_id}-${t.id}`),
    }));
    return {
      vertical_id: cell.vertical_id,
      seed: seed.length,
      forged: made.length,
      templates,
      complete: templates.every((t) => t.present),
    };
  });
  return {
    schema: "szl.scenario-forge-coverage/v1" as const,
    verticals: rows.length,
    templates: FORGE_TEMPLATES.length,
    complete_cells: rows.filter((r) => r.complete).length,
    seed_total: scenarios.length,
    forged_total: forged.length,
    rows,
  };
}
