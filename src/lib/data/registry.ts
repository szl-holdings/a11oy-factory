import rawProfile from "./profile.json";
import rawSnapshot from "./snapshot.json";
import type {
  FactoryProfile,
  FormulaBinding,
  VerticalCell,
} from "@/lib/types";

export const profile = rawProfile as FactoryProfile;
export const snapshot = rawSnapshot as {
  captured_at: string;
  counts: FactoryProfile["counts"];
  current_a11oy_honest_observation: {
    git_sha: string;
    locked_formula_count: number;
    persistence_claim: string;
    source_url: string;
  };
  current_killinchu_ready_observation: {
    durability_state: string;
    production_ready: boolean;
    source_url: string;
    status: string;
  };
  material_findings: string[];
  open_prs: FactoryProfile["current_open_prs"];
  schema: string;
};

export const PROFILE_SHA256 =
  "b213860bb1d44f8eb818d7e43c5d330d16dd27624988741e5b39889bcc66fd8e";

export const LOCKED_FORMULA_IDS = ["F1", "F4", "F7", "F11", "F12", "F18", "F22", "F24"];

export function formulaIds() {
  return new Set(profile.formula_bindings.map((item) => item.formula_id));
}

export function lockedFormulas(): FormulaBinding[] {
  return profile.formula_bindings.filter((item) =>
    LOCKED_FORMULA_IDS.includes(item.formula_id),
  );
}

export function verticalById(id: string): VerticalCell | undefined {
  return profile.vertical_cells.find((item) => item.vertical_id === id);
}

export const POLICY_REVISION = "policy.log-only.v6";
export const RUNTIME_REVISION = "runtime.factory.v6";
export const SOURCE_REVISION = "packet.estate-vertical-factory.v6";
