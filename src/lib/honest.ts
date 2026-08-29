import type { HonestContract } from "@/lib/types";
import { currentAdmission, OWNER_ORDER, OWNER_CERT } from "@/lib/admission";
import { profile, PROFILE_SHA256, snapshot } from "@/lib/data/registry";
import { loadLedger } from "@/lib/ledger";
import { validateProfile } from "@/lib/compiler";
import { spacePlan } from "@/lib/spaces";

export function buildHonest(): HonestContract {
  const admission = currentAdmission();
  return {
    schema: "szl.a11oy-honest/v1",
    runtime: "a11oy-factory",
    packet: "estate-vertical-factory-v6",
    captured_at: profile.captured_at,
    profile_sha256: PROFILE_SHA256,
    locked_formula_count: 8,
    formula_catalogue_count: profile.formula_bindings.length,
    persistence: {
      backend: "localStorage",
      durable: true,
      scope: "browser",
      signer: "unsigned-preview",
    },
    production_ready: false,
    nexus_admission: "CLASSIFIED_A11OY_INCUBATOR",
    admission_freeze: "LIFTED_BY_OWNER",
    green_light: admission.current.green_light,
    owner_order_id: OWNER_ORDER.order_id,
    killinchu_durability: "EPHEMERAL_IN_PUBLIC_SPACE",
    product_origin: {
      url: OWNER_CERT.measured.product_url,
      proof_url: OWNER_CERT.measured.proof_url,
      certification: OWNER_CERT.certification,
      owner_order_id: OWNER_CERT.order_id,
      http: OWNER_CERT.measured.http,
      health: OWNER_CERT.measured.health,
      signer: OWNER_CERT.measured.signer,
    },
    truth:
      "Owner order AO-2026-08-29-002 certifies a-11-oy.com as LIVE_PRODUCT_ORIGIN (HTTP 200, health ok, doctrine v11 LOCKED). Signer remains ABSENT — DSSE and FedRAMP are not certified. Factory runtime stays production_ready=false. Nexus is an A11oy incubator package. Lyte is the admitted protected design-partner cell.",
    generated_at: new Date().toISOString(),
  };
}

export function tabMatrix() {
  return profile.a11oy_routes.map((route) => ({
    route: route.route,
    owner: "product/release owner",
    purpose: route.current_role,
    source: route.source_url,
    captured_state: route.captured_state,
    target_route: route.target_route,
    priority: route.priority,
    recommended_action: route.recommended_action,
    accessibility: "WCAG 2.2 AA target",
    tests: route.acceptance,
    deprecation: route.captured_state === "TARGET" ? "not yet built in production" : "live or verify-current",
  }));
}

export function spacesHealth() {
  const plan = spacePlan();
  const spaces = profile.hugging_face_assets.filter((a) => a.category === "space");
  return {
    schema: "szl.spaces-health/v1",
    counted_in_hub: profile.counts.hf_spaces,
    displayed_on_a11oy_spaces_route: profile.counts.a11oy_spaces_route_displayed,
    live_org_page: plan.live_org_observation.live_org_page_2026_08_29,
    drift: profile.counts.hf_spaces - profile.counts.a11oy_spaces_route_displayed,
    canonical_public_target: plan.canonical_six,
    configured: plan.configured.map((space) => ({
      id: space.id,
      visibility: space.visibility,
      publish: space.publish,
      recommended_action: space.recommended_action,
    })),
    huggingface_token: plan.huggingface_token,
    hub_mutation: plan.hub_mutation,
    spaces: spaces.map((space) => ({
      id: space.asset_id,
      current_role: space.current_role,
      target_role: space.target_role,
      recommended_action: space.recommended_action,
      priority: space.priority,
      hub_revision: "snapshot-only",
      runtime_revision: "configured in factory, not bound on Hub",
    })),
    truth: plan.truth,
  };
}

export function genome() {
  return {
    schema: "szl.formula-genome/v1",
    locked_formula_count: 8,
    catalogue_count: profile.formula_bindings.length,
    lambda_axes_advisory: 13,
    lambda_axes_proved: 0,
    note: "Locked-8 is the proved set. Lambda is CONJECTURE/ADVISORY and never a pass/fail oracle. Observability must not say 5 proved formulas or 9 proved axes.",
    formulas: profile.formula_bindings.map((item) => ({
      formula_id: item.formula_id,
      name: item.name,
      proof_class: item.proof_class,
      grants_authority: item.grants_authority,
      allowed_runtime_binding: item.allowed_runtime_binding,
      prohibited_claim: item.prohibited_claim,
      verticals: item.verticals,
    })),
  };
}

export function readiness() {
  const errors = validateProfile();
  const ledger = typeof window === "undefined" ? { entries: [] } : loadLedger();
  const blocking = [
    errors.length ? "profile validation errors" : null,
    "Killinchu public Space reports EPHEMERAL durability",
    "a-11-oy.com is LIVE_PRODUCT_ORIGIN; DSSE and FedRAMP remain uncertified",
    "Hub and GitHub visibility cannot be mutated from this runtime",
    snapshot.current_killinchu_ready_observation.production_ready
      ? null
      : "public Killinchu production_ready=false",
  ].filter(Boolean);
  return {
    status: blocking.length ? "not-ready" : "ready",
    production_ready: false,
    durable_ledger: true,
    ledger_backend: "localStorage",
    ledger_entries: ledger.entries.length,
    profile_valid: errors.length === 0,
    admission: currentAdmission().current,
    owner_order_id: OWNER_ORDER.order_id,
    blocking,
    captured_killinchu: snapshot.current_killinchu_ready_observation,
  };
}

export function liveness() {
  return { status: "ok", role: "process liveness only", ready_is_separate: true };
}
