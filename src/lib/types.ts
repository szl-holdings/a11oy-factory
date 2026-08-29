export type EvidenceClass =
  | "MEASURED"
  | "REPORTED"
  | "SIMULATED"
  | "MODELED"
  | "PROVED"
  | "CONJECTURE"
  | "UNAVAILABLE";

export type RuntimeState =
  | "LOADING"
  | "READY"
  | "EMPTY"
  | "UNAVAILABLE"
  | "PARTIAL"
  | "DENIED"
  | "DEGRADED"
  | "ERROR";

export type DecisionStatus =
  | "PROPOSED"
  | "DENIED"
  | "ABSTAINED"
  | "ESCALATED"
  | "AWAITING_APPROVAL"
  | "APPROVED"
  | "EXECUTED"
  | "VERIFIED"
  | "ROLLED_BACK";

export type OutcomeState =
  | "PENDING"
  | "MEASURED"
  | "CORRECTED"
  | "REVOKED"
  | "UNAVAILABLE";

export type ProofClass =
  | "LOCKED-PROVEN"
  | "SEMANTIC-VERIFIED"
  | "CONJECTURE/ADVISORY";

export type SpaceVisibility = "public" | "protected" | "private";

export type PolicyMode = "LOG_ONLY" | "ENFORCE";

export type PolicyEffect =
  | "DENY"
  | "ABSTAIN"
  | "ESCALATE"
  | "PROPOSE"
  | "ALLOW_WITH_APPROVAL";

export interface Leader {
  name: string;
  pattern: string;
  url: string;
}

export interface DataPolicy {
  public: string[];
  protected: string[];
  training_use: string;
}

export interface VerticalCell {
  schema: "szl.vertical-cell/v1";
  vertical_id: string;
  display_name: string;
  portfolio_role: string;
  stage: string;
  space_visibility: SpaceVisibility;
  public_launch: string;
  buyer: string;
  decision_problem: string;
  original_szl_design: string;
  hf_space_id: string;
  core_workflows: string[];
  human_authority: string[];
  allowed_actions: string[];
  prohibited_actions: string[];
  formula_bindings: string[];
  success_metrics: string[];
  negative_tests: string[];
  leaders: Leader[];
  data_policy: DataPolicy;
}

export interface FormulaBinding {
  formula_id: string;
  name: string;
  proof_class: ProofClass;
  allowed_runtime_binding: string;
  prohibited_claim: string;
  verticals: string;
  grants_authority: boolean;
  required_binding_evidence: string;
  source_url: string;
}

export interface RepositoryRow {
  index: number;
  repository: string;
  visibility: string;
  archived: boolean;
  size_kb_captured: number;
  current_portfolio: string;
  target_class: string;
  target: string;
  recommended_action: string;
  priority: string;
  investor_role: string;
  vertical_binding: string;
  accountable_role: string;
  one_by_one_audit_focus: string;
  blocking_exit_evidence: string;
  new_since_payload4: boolean;
  source_url: string;
}

export interface HfAsset {
  category: string;
  asset_id: string;
  current_role: string;
  target_role: string;
  recommended_action: string;
  priority: string;
  audit_focus: string;
  reason: string;
  source_url: string;
}

export interface RouteRow {
  route: string;
  captured_state: string;
  current_role: string;
  target_route: string;
  recommended_action: string;
  priority: string;
  finding: string;
  acceptance: string;
  source_url: string;
}

export interface KillinchuRoute {
  route: string;
  role: string;
  recommended_action: string;
  priority: string;
  finding: string;
  public_safety_boundary: string;
  acceptance: string;
  source_url: string;
}

export interface OpenPr {
  disposition: string;
  number: number;
  reason: string;
  repository: string;
  source_url: string;
  title: string;
}

export interface FrontierItem {
  id: string;
  name: string;
  novelty: string;
  build: string;
  priority: string;
  acceptance: string[];
}

export interface AdmissionFreeze {
  blocks: string[];
  exceptions: string[];
  exit: string[];
  reason: string;
  required: boolean;
}

export interface ProductHierarchy {
  category: string;
  company: string;
  core_product: { name: string; one_sentence: string; role: string };
  internal_engine: { name: string; role: string; rule: string };
  primary_vertical: {
    commercial_name: string;
    name: string;
    role: string;
  };
  adjacent_vertical: {
    commercial_name: string;
    name: string;
    role: string;
  };
  partner_gated_vertical: { name: string; role: string };
  public_reference: { name: string; role: string };
  retired_or_incubated: string[];
}

export interface FactoryCounts {
  a11oy_routes_in_audit: number;
  a11oy_spaces_route_displayed: number;
  github_archived: number;
  github_private: number;
  github_public: number;
  github_public_page_displayed: number;
  github_repositories_authenticated: number;
  hf_assets_in_audit: number;
  hf_buckets: number;
  hf_collections: number;
  hf_datasets: number;
  hf_kernels: number;
  hf_models_dedicated_listing: number;
  hf_models_org_front: number;
  hf_spaces: number;
  killinchu_routes_in_audit: number;
  open_prs_authenticated: number;
  vertical_cells: number;
}

export interface FactoryProfile {
  schema: string;
  captured_at: string;
  mission: string;
  primary_recommendation: string;
  truth_boundary: string[];
  counts: FactoryCounts;
  admission_freeze: AdmissionFreeze;
  canonical_public_spaces_target: string[];
  product_hierarchy: ProductHierarchy;
  formula_bindings: FormulaBinding[];
  vertical_cells: VerticalCell[];
  repositories: RepositoryRow[];
  hugging_face_assets: HfAsset[];
  a11oy_routes: RouteRow[];
  killinchu_routes: KillinchuRoute[];
  current_open_prs: OpenPr[];
  frontier_program: FrontierItem[];
  leader_matrix: unknown[];
}

export interface EvidenceItem {
  evidence_id: string;
  class: EvidenceClass;
  digest: string;
  freshness: string;
  label: string;
  detail?: string;
}

export interface Scenario {
  scenario_id: string;
  vertical_id: string;
  title: string;
  summary: string;
  workflow: string;
  expected: DecisionStatus;
  evidence: EvidenceItem[];
  facts: Record<string, string | number | boolean>;
  negative?: boolean;
}

export interface DecisionReceipt {
  schema: "szl.vertical-decision-receipt/v1";
  vertical_id: string;
  decision_id: string;
  tenant_id: string;
  scenario_id: string;
  source_revision: string;
  runtime_revision: string;
  manifest_digest: string;
  prev_hash: string;
  hash: string;
  evidence: EvidenceItem[];
  policy: {
    mode: PolicyMode;
    revision: string;
    effect: PolicyEffect;
    reasons: string[];
    formula_grants_authority: false;
    shadow?: {
      candidate_effect: PolicyEffect;
      candidate_reasons: string[];
      differs: boolean;
    };
  };
  authority: {
    required: string[];
    actor: string;
    approved: boolean;
  };
  proposal: {
    action: string;
    summary: string;
    cannot_grant_authority: true;
  };
  decision: {
    status: DecisionStatus;
    rationale: string;
  };
  outcome_state: OutcomeState;
  created_at: string;
  limitations: string[];
}

export interface HonestContract {
  schema: "szl.a11oy-honest/v1";
  runtime: string;
  packet: string;
  captured_at: string;
  profile_sha256: string;
  locked_formula_count: 8;
  formula_catalogue_count: number;
  persistence: {
    backend: string;
    durable: boolean;
    scope: string;
    signer: string;
  };
  production_ready: false;
  nexus_admission: "BLOCKED" | "CLASSIFIED_A11OY_INCUBATOR";
  admission_freeze: "IN_EFFECT" | "LIFTED_BY_OWNER";
  green_light: "PROPOSED" | "APPROVED";
  owner_order_id: string;
  killinchu_durability: "EPHEMERAL_IN_PUBLIC_SPACE";
  truth: string;
  generated_at: string;
}

export interface AdmissionReceipt {
  schema: "szl.owner-admission-receipt/v1";
  order_id: string;
  decision_id: string;
  actor: string;
  approved: true;
  effect: "GREEN_LIGHT";
  freeze: "LIFTED_BY_OWNER";
  nexus: "CLASSIFIED_A11OY_INCUBATOR";
  lyte: "ADMITTED_PROTECTED_DESIGN_PARTNER";
  frontier: "OPEN";
  production_ready: false;
  formula_grants_authority: false;
  still_prohibits: string[];
  instruction: string;
  prev_hash: string;
  hash: string;
  created_at: string;
  limitations: string[];
}
