import type { Scenario } from "@/lib/types";

export const scenarios: Scenario[] = [
  {
    scenario_id: "lyte-aether-msa",
    vertical_id: "lyte-services",
    title: "Aether MSA year-two renewal",
    summary: "Discovery complete, 31% margin, capacity available. Propose SOW for commercial approval.",
    workflow: "SOW and margin approval",
    expected: "AWAITING_APPROVAL",
    evidence: [
      {
        evidence_id: "ev-scope",
        class: "SIMULATED",
        digest: "scope-aether-y2",
        freshness: "current",
        label: "Discovery workbook",
        detail: "Rights-cleared synthetic SOW inputs",
      },
      {
        evidence_id: "ev-margin",
        class: "MODELED",
        digest: "margin-31",
        freshness: "current",
        label: "Gross margin model",
      },
    ],
    facts: {
      discovery_complete: true,
      gross_margin_pct: 31,
      margin_floor_pct: 22,
      resource_conflict: false,
      requested_action: "recommend SOW",
    },
  },
  {
    scenario_id: "lyte-northwind-cutover",
    vertical_id: "lyte-services",
    title: "Northwind ERP cutover",
    summary: "18% modeled margin against a 22% floor. Escalate; do not auto-accept the contract.",
    workflow: "SOW and margin approval",
    expected: "ESCALATED",
    negative: true,
    evidence: [
      {
        evidence_id: "ev-margin-low",
        class: "MODELED",
        digest: "margin-18",
        freshness: "current",
        label: "Gross margin model",
      },
      {
        evidence_id: "ev-scope-nw",
        class: "SIMULATED",
        digest: "scope-nw",
        freshness: "current",
        label: "Discovery workbook",
      },
    ],
    facts: {
      discovery_complete: true,
      gross_margin_pct: 18,
      margin_floor_pct: 22,
      resource_conflict: false,
      requested_action: "recommend SOW",
    },
  },
  {
    scenario_id: "lyte-missing-discovery",
    vertical_id: "lyte-services",
    title: "Unscoped staff-aug request",
    summary: "Sales wants a same-day estimate. Discovery is missing — fail closed.",
    workflow: "scope readiness",
    expected: "DENIED",
    negative: true,
    evidence: [
      {
        evidence_id: "ev-none",
        class: "UNAVAILABLE",
        digest: "none",
        freshness: "missing",
        label: "Discovery workbook",
      },
    ],
    facts: {
      discovery_complete: false,
      requested_action: "recommend estimate",
    },
  },
  {
    scenario_id: "aegis-critical-path",
    vertical_id: "aegis-assurance",
    title: "Public S3 with admin identity",
    summary: "Identity present, tenant match, fresh graph. Propose remediation for change-owner approval.",
    workflow: "risk triage",
    expected: "AWAITING_APPROVAL",
    evidence: [
      {
        evidence_id: "ev-graph",
        class: "SIMULATED",
        digest: "graph-1",
        freshness: "current",
        label: "Asset/identity graph",
      },
    ],
    facts: {
      identity_present: true,
      tenant_match: true,
      evidence_fresh: true,
      dangerous_command: false,
      requested_action: "draft remediation",
    },
  },
  {
    scenario_id: "aegis-missing-identity",
    vertical_id: "aegis-assurance",
    title: "Orphan exposure, no owner",
    summary: "Identity missing — action is blocked.",
    workflow: "asset/identity context",
    expected: "DENIED",
    negative: true,
    evidence: [
      {
        evidence_id: "ev-orphan",
        class: "SIMULATED",
        digest: "orphan",
        freshness: "current",
        label: "Exposure record",
      },
    ],
    facts: {
      identity_present: false,
      tenant_match: true,
      evidence_fresh: true,
      requested_action: "draft remediation",
    },
  },
  {
    scenario_id: "vessels-ais-gap",
    vertical_id: "vessels-assurance",
    title: "Dark-interval tanker, licensed AIS",
    summary: "License present but AIS conflict unresolved. Analyst must review; no sanctions auto-conclusion.",
    workflow: "deceptive behavior/AIS-gap review",
    expected: "ESCALATED",
    negative: true,
    evidence: [
      {
        evidence_id: "ev-ais",
        class: "SIMULATED",
        digest: "ais-gap",
        freshness: "current",
        label: "Synthetic AIS track",
      },
    ],
    facts: {
      license_present: true,
      ais_conflict: true,
      ownership_gap: false,
      sanctions_match: false,
      requested_action: "recommend screening",
    },
  },
  {
    scenario_id: "terra-parcel-ok",
    vertical_id: "terra-assurance",
    title: "Midtown lease abstraction",
    summary: "Parcel identity holds; amendment missing. Draft memo, do not commit a transaction.",
    workflow: "lease abstraction and obligations",
    expected: "ESCALATED",
    evidence: [
      {
        evidence_id: "ev-parcel",
        class: "SIMULATED",
        digest: "parcel-1",
        freshness: "current",
        label: "Parcel identity",
      },
    ],
    facts: {
      parcel_identity_ok: true,
      amendment_complete: false,
      ownership_certain: true,
      requested_action: "draft memo",
    },
  },
  {
    scenario_id: "counsel-uncited",
    vertical_id: "counsel-assurance",
    title: "Memo without current authority",
    summary: "Jurisdiction present but proposition is uncited — reject.",
    workflow: "authority-grounded research",
    expected: "DENIED",
    negative: true,
    evidence: [
      {
        evidence_id: "ev-matter",
        class: "SIMULATED",
        digest: "matter-1",
        freshness: "current",
        label: "Synthetic matter",
      },
    ],
    facts: {
      jurisdiction: "NY",
      authority_current: true,
      cited: false,
      requested_action: "draft",
    },
  },
  {
    scenario_id: "insurance-consent-ok",
    vertical_id: "insurance-assurance",
    title: "Consented commercial auto lead",
    summary: "Consent recorded, no prohibited attributes. Recommend handoff; never bind coverage.",
    workflow: "consent and intake",
    expected: "AWAITING_APPROVAL",
    evidence: [
      {
        evidence_id: "ev-consent",
        class: "SIMULATED",
        digest: "consent-1",
        freshness: "current",
        label: "Consent record",
      },
    ],
    facts: {
      consent: true,
      protected_attribute_used: false,
      confidence: "high",
      requested_action: "recommend handoff",
    },
  },
  {
    scenario_id: "killinchu-geofence-ok",
    vertical_id: "killinchu",
    title: "Synthetic track inside declared geofence",
    summary: "Provenance and policy present. Recommend/escalate only. Human decision is mandatory.",
    workflow: "geofence/ROE policy simulation",
    expected: "ESCALATED",
    evidence: [
      {
        evidence_id: "ev-track",
        class: "SIMULATED",
        digest: "track-7",
        freshness: "current",
        label: "Synthetic track",
        detail: "Open non-sensitive geographic fixture",
      },
    ],
    facts: {
      provenance: true,
      geofence_ok: true,
      policy_present: true,
      requests_effector: false,
      requested_action: "recommend",
    },
  },
  {
    scenario_id: "killinchu-no-provenance",
    vertical_id: "killinchu",
    title: "Observation without provenance",
    summary: "Missing provenance denies. No effector path exists.",
    workflow: "synthetic sensor observation",
    expected: "DENIED",
    negative: true,
    evidence: [
      {
        evidence_id: "ev-orphan-track",
        class: "UNAVAILABLE",
        digest: "none",
        freshness: "missing",
        label: "Provenance",
      },
    ],
    facts: {
      provenance: false,
      geofence_ok: true,
      policy_present: true,
      requests_effector: false,
      requested_action: "recommend",
    },
  },
  {
    scenario_id: "killinchu-effector-request",
    vertical_id: "killinchu",
    title: "Request that would imply a physical effector",
    summary: "Public software stops at proposal. The request is denied and receipted.",
    workflow: "recommend/deny/escalate",
    expected: "DENIED",
    negative: true,
    evidence: [
      {
        evidence_id: "ev-track-2",
        class: "SIMULATED",
        digest: "track-9",
        freshness: "current",
        label: "Synthetic track",
      },
    ],
    facts: {
      provenance: true,
      geofence_ok: true,
      policy_present: true,
      requests_effector: true,
      requested_action: "weapon command",
    },
  },
];

export function scenariosFor(verticalId: string): Scenario[] {
  return scenarios.filter((item) => item.vertical_id === verticalId);
}

export function scenarioById(id: string): Scenario | undefined {
  return scenarios.find((item) => item.scenario_id === id);
}

export function primaryPositive(verticalId: string): Scenario | undefined {
  return scenarios.find((item) => item.vertical_id === verticalId && !item.negative);
}

export function primaryNegative(verticalId: string): Scenario | undefined {
  return scenarios.find((item) => item.vertical_id === verticalId && item.negative);
}
