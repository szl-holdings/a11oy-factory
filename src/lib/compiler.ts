import type { VerticalCell } from "@/lib/types";
import { digestText, sha256Json } from "@/lib/hash";
import { POLICY_REVISION, profile, RUNTIME_REVISION } from "@/lib/data/registry";

const VERTICAL_ID = /^[a-z0-9-]+$/;
const HF_SPACE_ID = /^SZLHOLDINGS\/[A-Za-z0-9._-]+$/;

function requireString(manifest: VerticalCell, key: keyof VerticalCell, errors: string[]) {
  const value = manifest[key];
  if (typeof value !== "string" || !value.trim()) {
    errors.push(`${String(key)}: expected non-empty string`);
  }
}

function requireStringList(
  manifest: VerticalCell,
  key: keyof VerticalCell,
  errors: string[],
) {
  const value = manifest[key];
  if (!Array.isArray(value) || value.length < 1) {
    errors.push(`${String(key)}: expected at least 1 entries`);
    return;
  }
  if (value.some((item) => typeof item !== "string" || !item.trim())) {
    errors.push(`${String(key)}: every entry must be a non-empty string`);
  }
}

export function validateVertical(
  manifest: VerticalCell,
  formulaIds: Set<string>,
): string[] {
  const errors: string[] = [];
  if (manifest.schema !== "szl.vertical-cell/v1") {
    errors.push("schema must be szl.vertical-cell/v1");
  }
  (
    [
      "vertical_id",
      "display_name",
      "portfolio_role",
      "stage",
      "space_visibility",
      "public_launch",
      "buyer",
      "decision_problem",
      "original_szl_design",
      "hf_space_id",
    ] as const
  ).forEach((key) => requireString(manifest, key, errors));
  (
    [
      "core_workflows",
      "human_authority",
      "allowed_actions",
      "prohibited_actions",
      "formula_bindings",
      "success_metrics",
      "negative_tests",
    ] as const
  ).forEach((key) => requireStringList(manifest, key, errors));

  if (manifest.vertical_id && !VERTICAL_ID.test(manifest.vertical_id)) {
    errors.push("vertical_id must match ^[a-z0-9-]+$");
  }
  if (!["public", "protected", "private"].includes(manifest.space_visibility)) {
    errors.push("space_visibility must be public, protected, or private");
  }
  if (manifest.hf_space_id && !HF_SPACE_ID.test(manifest.hf_space_id)) {
    errors.push("hf_space_id must be under SZLHOLDINGS");
  }
  if (!Array.isArray(manifest.leaders) || manifest.leaders.length < 2) {
    errors.push("leaders: expected at least two public leader patterns");
  }
  const unknown = manifest.formula_bindings.filter((id) => !formulaIds.has(id));
  if (unknown.length) errors.push(`unknown formula bindings: ${unknown.join(", ")}`);

  const forbidden = manifest.prohibited_actions.join(" ").toLowerCase();
  if (manifest.vertical_id === "killinchu") {
    for (const phrase of ["weapon command", "target engagement", "physical effector"]) {
      if (!forbidden.includes(phrase)) {
        errors.push(`killinchu prohibited_actions must include '${phrase}'`);
      }
    }
    if (manifest.space_visibility !== "public") {
      errors.push("killinchu is the declared public synthetic reference");
    }
  } else if (manifest.space_visibility === "public") {
    errors.push(
      "only Killinchu may be public before vertical admission; use protected/private for other cells",
    );
  }
  return errors;
}

export function validateProfile(): string[] {
  const errors: string[] = [];
  if (profile.schema !== "szl.estate-vertical-factory-profile/v6") {
    errors.push("profile schema must be szl.estate-vertical-factory-profile/v6");
  }
  const formulaIds = new Set<string>();
  for (const item of profile.formula_bindings) {
    if (formulaIds.has(item.formula_id)) {
      errors.push(`duplicate formula_id: ${item.formula_id}`);
    }
    formulaIds.add(item.formula_id);
    if (item.grants_authority !== false) {
      errors.push(`${item.formula_id}: grants_authority must be false`);
    }
  }
  for (const vertical of profile.vertical_cells) {
    errors.push(...validateVertical(vertical, formulaIds));
  }
  const nexus = profile.repositories.filter((r) => r.repository === "szl-holdings/nexus");
  if (nexus.length !== 1) errors.push("nexus must appear exactly once");
  else if (nexus[0].recommended_action !== "BLOCK_AND_CLASSIFY") {
    errors.push("nexus must remain admission-blocked");
  }
  if (profile.canonical_public_spaces_target.length > 6) {
    errors.push("canonical public Space target exceeds six");
  }
  return errors;
}

export function routeContract(manifest: VerticalCell) {
  return {
    schema: "szl.vertical-route-contract/v1",
    vertical_id: manifest.vertical_id,
    routes: [
      { path: "/", role: "vertical product explanation", access: manifest.space_visibility, state: manifest.stage },
      {
        path: "/decision",
        role: "governed decision theatre",
        methods: ["GET", "POST"],
        mutation_boundary:
          "POST creates a proposal or decision record only; external action requires separate authority",
      },
      { path: "/verify", role: "offline-capable receipt verification", methods: ["GET"] },
      { path: "/healthz", role: "process liveness only", methods: ["GET", "HEAD"] },
      { path: "/readyz", role: "durable dependency-aware readiness", methods: ["GET", "HEAD"] },
      {
        path: "/version",
        role: "source, artifact, policy, model, data, and manifest identity",
        methods: ["GET", "HEAD"],
      },
      {
        path: "/evidence",
        role: "current evidence, limitations, incidents, and release records",
        methods: ["GET", "HEAD"],
      },
    ],
    required_ui_states: [
      "LOADING",
      "READY",
      "EMPTY",
      "UNAVAILABLE",
      "PARTIAL",
      "DENIED",
      "DEGRADED",
      "ERROR",
    ],
  };
}

export function policyContract(manifest: VerticalCell) {
  return {
    schema: "szl.vertical-policy-contract/v1",
    vertical_id: manifest.vertical_id,
    human_authority: manifest.human_authority,
    allowed_actions: manifest.allowed_actions,
    prohibited_actions: manifest.prohibited_actions,
    formula_bindings: manifest.formula_bindings,
    formula_grants_authority: false,
    default_effect: "DENY",
    candidate_policy_mode: "LOG_ONLY",
    policy_revision: POLICY_REVISION,
    runtime_revision: RUNTIME_REVISION,
  };
}

export function uiContract(manifest: VerticalCell) {
  return {
    schema: "szl.evidence-bearing-ui/v1",
    vertical_id: manifest.vertical_id,
    first_fold: {
      buyer: manifest.buyer,
      decision_problem: manifest.decision_problem,
      primary_workflow: manifest.core_workflows[0],
      primary_cta: "Run governed scenario",
      evidence_cta: "Verify a decision receipt",
    },
    component_truth_fields: [
      "evidence_class",
      "runtime_state",
      "authority_state",
      "freshness",
      "source_digest",
      "policy_revision",
      "replay_url",
      "limitations",
    ],
    required_states: routeContract(manifest).required_ui_states,
  };
}

export function evaluationPlan(manifest: VerticalCell) {
  return {
    schema: "szl.vertical-evaluation-plan/v1",
    vertical_id: manifest.vertical_id,
    stage: manifest.stage,
    success_metrics: manifest.success_metrics,
    negative_tests: manifest.negative_tests,
  };
}

export function investorDemo(manifest: VerticalCell) {
  return {
    schema: "szl.investor-decision-theatre/v1",
    vertical_id: manifest.vertical_id,
    display_name: manifest.display_name,
    three_minute_sequence: [
      { step: 1, show: "buyer and costly decision problem", content: manifest.decision_problem },
      { step: 2, show: "source and evidence context", content: "Exact inputs, freshness, rights, and limitations" },
      { step: 3, show: "model or deterministic proposal", content: "Proposal cannot grant authority" },
      { step: 4, show: "policy and human authority", content: manifest.human_authority },
      { step: 5, show: "positive decision and receipt", content: "Verify source, policy, authority, and postcondition" },
      { step: 6, show: "negative decision", content: manifest.negative_tests[0] },
      { step: 7, show: "replay and outcome", content: "No-side-effect replay plus current measured outcome" },
    ],
    claims_boundary:
      "No production, customer, ROI, safety, or superiority claim without current evidence generated from the same release record.",
  };
}

export function spaceReleasePlan(manifest: VerticalCell, manifestDigest: string) {
  return {
    schema: "szl.vertical-space-release-plan/v1",
    vertical_id: manifest.vertical_id,
    space_id: manifest.hf_space_id,
    target_visibility: manifest.space_visibility,
    public_launch: manifest.public_launch,
    source_repository: "szl-holdings/platform/apps/vertical-cells + packages/vertical-runtime",
    deployment_pattern: "one immutable runtime image plus one signed vertical manifest",
    manifest_digest: manifestDigest,
    one_writer: true,
    admission_gates: [
      "source and license",
      "data rights and privacy",
      "policy and human authority",
      "frozen evaluations and negative tests",
      "security and tenant isolation",
      "accessibility and performance",
      "durable readiness",
      "cost and capacity",
      "incident and rollback",
      "claims review",
    ],
  };
}

export interface CompiledCell {
  vertical_id: string;
  valid: boolean;
  errors: string[];
  manifest_digest: string;
  contracts: {
    route: ReturnType<typeof routeContract>;
    policy: ReturnType<typeof policyContract>;
    ui: ReturnType<typeof uiContract>;
    evaluation: ReturnType<typeof evaluationPlan>;
    investor: ReturnType<typeof investorDemo>;
    space: ReturnType<typeof spaceReleasePlan>;
  };
}

export async function compileVertical(
  manifest: VerticalCell,
  formulaIds: Set<string>,
): Promise<CompiledCell> {
  const errors = validateVertical(manifest, formulaIds);
  const manifest_digest = await sha256Json(manifest);
  return {
    vertical_id: manifest.vertical_id,
    valid: errors.length === 0,
    errors,
    manifest_digest,
    contracts: {
      route: routeContract(manifest),
      policy: policyContract(manifest),
      ui: uiContract(manifest),
      evaluation: evaluationPlan(manifest),
      investor: investorDemo(manifest),
      space: spaceReleasePlan(manifest, manifest_digest),
    },
  };
}

export async function compileAll(formulaIds: Set<string>): Promise<CompiledCell[]> {
  const compiled: CompiledCell[] = [];
  for (const vertical of [...profile.vertical_cells].sort((a, b) =>
    a.vertical_id.localeCompare(b.vertical_id),
  )) {
    compiled.push(await compileVertical(vertical, formulaIds));
  }
  return compiled;
}

export async function factoryIdentityDigest(): Promise<string> {
  return digestText(
    `${profile.schema}|${profile.captured_at}|${profile.counts.github_repositories_authenticated}`,
  );
}
