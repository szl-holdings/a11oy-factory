import type { AdmissionReceipt, SpaceVisibility, VerticalCell } from "@/lib/types";
import { canonicalJson, digestText } from "@/lib/hash";
import { profile } from "@/lib/data/registry";

const STORAGE_KEY = "a11oy.admission.v1";
const GENESIS = "0".repeat(64);

export const OWNER_ORDER = {
  schema: "szl.owner-admission-order/v1" as const,
  order_id: "AO-2026-08-29-001",
  issued_at: "2026-08-29T04:39:00.000Z",
  approved_at: "2026-08-29T10:44:00.000Z",
  actor: "estate owner",
  authority:
    "Packet 6 freeze exception: owner-approved customer-critical fix; registry and compiler implementation",
  instruction:
    "Lift the admission freeze. Classify szl-holdings/nexus as an A11oy incubator package. Admit Lyte Services as the first protected design-partner cell. Open frontier program N1–N8 in this factory preview.",
  github: {
    factory_repo: "szl-holdings/a11oy-factory",
    url: "https://github.com/szl-holdings/a11oy-factory",
    visibility: "public",
    bind: "BIND_AS_A11OY_PACKAGE",
  },
  huggingface: {
    intended_space: "SZLHOLDINGS/a11oy-factory",
    sdk: "docker",
    status: "PUBLISHED_PRIVATE",
    blocker: "Hub card exists. Docker is fetching metadata. Not a production certificate. Not a seventh public Space.",
    url: "https://huggingface.co/spaces/SZLHOLDINGS/a11oy-factory",
    published_via: "szl-holdings/szl-experiments publish-sibling-spaces",
  },
  still_prohibits: [
    "new top-level product name",
    "DSSE signing claims while signer is ABSENT",
    "FedRAMP / IL5 / ATO accreditation",
    "Killinchu public production_ready=true",
    "Hub visibility mutation from this runtime",
  ] as const,
  effects: {
    freeze: "LIFTED_BY_OWNER" as const,
    green_light: "APPROVED" as const,
    nexus: {
      repository: "szl-holdings/nexus",
      classification: "A11OY_INCUBATOR_PACKAGE" as const,
      target_class: "INCUBATE_THEN_BIND",
      recommended_action: "BIND_AS_A11OY_PACKAGE",
      public_product: false,
      note: "Not a second flagship and not a new public product name. Development is unfrozen for classification and package binding only.",
    },
    lyte: {
      vertical_id: "lyte-services",
      admission: "ADMITTED_PROTECTED_DESIGN_PARTNER" as const,
      space_visibility: "protected" as SpaceVisibility,
      public_launch: "PROTECTED_PILOT_OPEN — public launch still blocked until measured pilot evidence",
    },
    frontier: "OPEN" as const,
  },
  truth_boundary: [
    "Packet 6 snapshot remains the captured estate evidence.",
    "This factory source is published at szl-holdings/a11oy-factory.",
    "Hugging Face Space SZLHOLDINGS/a11oy-factory is published private via szl-experiments. Docker metadata is fetching; this is not a production certificate.",
    "Formulas still never grant authority.",
    "Killinchu remains the only public synthetic reference.",
    "Green light is an owner admission decision. a-11-oy.com is certified LIVE_PRODUCT_ORIGIN from measured probes; DSSE signing and FedRAMP remain uncertified.",
  ] as const,
};

export const OWNER_CERT = {
  schema: "szl.owner-product-origin-cert/v1" as const,
  order_id: "AO-2026-08-29-002",
  issued_at: "2026-08-29T15:56:00.000Z",
  actor: "estate owner / CTO overlay",
  instruction: "Certify a-11-oy.com as the LIVE product origin front door from measured probes.",
  certification: "LIVE_PRODUCT_ORIGIN" as const,
  measured: {
    product_url: "https://a-11-oy.com",
    proof_url: "https://a11oy.net",
    http: 200,
    health: "ok",
    doctrine: "v11 LOCKED 749/14/163 @ c7c0ba17",
    honest_git_sha: "9208362d2a510f2d23f6a1bc80ee82ecf5dd580e",
    signer: "ABSENT",
    locked_formulas: ["F1", "F4", "F7", "F11", "F12", "F18", "F19", "F22"],
    lambda: "Conjecture 1 — not a theorem",
    evidence_class: "MEASURED" as const,
  },
  not_certified: [
    "DSSE / persistent signer",
    "FedRAMP / IL5 / ATO",
    "Killinchu public production_ready",
    "this factory runtime (a11oy-factory remains production_ready=false)",
  ],
} as const;

export type OwnerOrder = typeof OWNER_ORDER;

export interface CellRuntimeOverlay {
  admitted: boolean;
  label: string;
  public_launch: string;
  space_visibility: SpaceVisibility;
}

const CELL_OVERLAY: Record<string, CellRuntimeOverlay> = {
  "lyte-services": {
    admitted: true,
    label: "ADMITTED protected pilot",
    public_launch: OWNER_ORDER.effects.lyte.public_launch,
    space_visibility: "protected",
  },
  "aegis-assurance": {
    admitted: false,
    label: "next after Lyte traction",
    public_launch: "blocked until Lyte traction and security gate",
    space_visibility: "protected",
  },
  "vessels-assurance": {
    admitted: false,
    label: "partner and data gate",
    public_launch: "blocked until licensed data and maritime partner",
    space_visibility: "private",
  },
  "terra-assurance": {
    admitted: false,
    label: "incubated",
    public_launch: "blocked until data rights and design partner",
    space_visibility: "private",
  },
  "counsel-assurance": {
    admitted: false,
    label: "qualified partner gate",
    public_launch: "blocked until qualified legal partner",
    space_visibility: "private",
  },
  "insurance-assurance": {
    admitted: false,
    label: "refactor existing",
    public_launch: "synthetic module allowed after refactor",
    space_visibility: "protected",
  },
  killinchu: {
    admitted: true,
    label: "PUBLIC synthetic reference",
    public_launch: "keep public only as simulated proposal system",
    space_visibility: "public",
  },
};

export function cellOverlay(verticalId: string): CellRuntimeOverlay {
  return (
    CELL_OVERLAY[verticalId] ?? {
      admitted: false,
      label: "not admitted",
      public_launch: "blocked",
      space_visibility: "private",
    }
  );
}

export function overlayVertical(vertical: VerticalCell): VerticalCell {
  const overlay = cellOverlay(vertical.vertical_id);
  return {
    ...vertical,
    space_visibility: overlay.space_visibility,
    public_launch: overlay.public_launch,
    stage: overlay.admitted ? `${vertical.stage}+ADMITTED` : vertical.stage,
  };
}

interface AdmissionStore {
  schema: "szl.owner-admission-ledger/v1";
  genesis: string;
  receipts: AdmissionReceipt[];
}

function emptyStore(): AdmissionStore {
  return { schema: "szl.owner-admission-ledger/v1", genesis: GENESIS, receipts: [] };
}

function loadStore(): AdmissionStore {
  if (typeof window === "undefined") return emptyStore();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyStore();
    const parsed = JSON.parse(raw) as AdmissionStore;
    if (!Array.isArray(parsed.receipts)) return emptyStore();
    return parsed;
  } catch {
    return emptyStore();
  }
}

function saveStore(store: AdmissionStore): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

export function loadOwnerApproval(): AdmissionReceipt | null {
  const store = loadStore();
  return store.receipts.find((item) => item.order_id === OWNER_ORDER.order_id) ?? store.receipts.at(-1) ?? null;
}

async function unsignedApproval(actor: string, prev: string, createdAt: string): Promise<Omit<AdmissionReceipt, "hash">> {
  return {
    schema: "szl.owner-admission-receipt/v1",
    order_id: OWNER_ORDER.order_id,
    decision_id: `adm_${OWNER_ORDER.order_id}`,
    actor,
    approved: true,
    effect: "GREEN_LIGHT",
    freeze: "LIFTED_BY_OWNER",
    nexus: "CLASSIFIED_A11OY_INCUBATOR",
    lyte: "ADMITTED_PROTECTED_DESIGN_PARTNER",
    frontier: "OPEN",
    production_ready: false,
    formula_grants_authority: false,
    still_prohibits: [...OWNER_ORDER.still_prohibits],
    instruction: OWNER_ORDER.instruction,
    prev_hash: prev,
    created_at: createdAt,
    limitations: [...OWNER_ORDER.truth_boundary],
  };
}

export async function approveOwnerOrder(actor = OWNER_ORDER.actor): Promise<AdmissionReceipt> {
  const store = loadStore();
  const existing = store.receipts.find((item) => item.order_id === OWNER_ORDER.order_id);
  if (existing) return existing;
  const prev = store.receipts.at(-1)?.hash ?? store.genesis;
  const unsigned = await unsignedApproval(actor, prev, new Date().toISOString());
  const hash = await digestText(canonicalJson(unsigned));
  const receipt: AdmissionReceipt = { ...unsigned, hash };
  store.receipts.push(receipt);
  saveStore(store);
  return receipt;
}

export async function ensureOwnerApproval(): Promise<AdmissionReceipt> {
  return approveOwnerOrder();
}

export async function verifyAdmissionReceipt(receipt: AdmissionReceipt) {
  const findings: string[] = [];
  if (receipt.schema !== "szl.owner-admission-receipt/v1") findings.push("unknown admission schema");
  if (receipt.approved !== true) findings.push("green light is not approved");
  if (receipt.formula_grants_authority !== false) findings.push("formula must not grant authority");
  if (receipt.production_ready !== false) findings.push("admission receipt cannot certify production");
  const { hash, ...rest } = receipt;
  const expected = await digestText(canonicalJson(rest));
  if (expected !== hash) findings.push("hash does not match canonical body");
  const stored = loadOwnerApproval();
  const inStore = stored?.hash === receipt.hash;
  if (!inStore) findings.push("receipt is not in the local admission ledger (self-contained check only)");
  return {
    ok: findings.filter((f) => !f.startsWith("receipt is not")).length === 0,
    findings,
    inStore,
  };
}

export function currentAdmission() {
  const freeze = profile.admission_freeze;
  const receipt = loadOwnerApproval();
  return {
    schema: "szl.current-admission/v1" as const,
    packet_freeze_required: freeze.required,
    packet_reason: freeze.reason,
    current: {
      freeze: OWNER_ORDER.effects.freeze,
      green_light: OWNER_ORDER.effects.green_light,
      nexus: OWNER_ORDER.effects.nexus.classification,
      lyte: OWNER_ORDER.effects.lyte.admission,
      frontier: OWNER_ORDER.effects.frontier,
      production_ready: false as const,
      github: OWNER_ORDER.github,
      huggingface: OWNER_ORDER.huggingface,
      product_origin: OWNER_CERT.certification,
    },
    order: OWNER_ORDER,
    cert: OWNER_CERT,
    receipt: receipt
      ? {
          decision_id: receipt.decision_id,
          hash: receipt.hash,
          actor: receipt.actor,
          approved: receipt.approved,
          created_at: receipt.created_at,
        }
      : null,
    historical_blocks: freeze.blocks,
    historical_exit: freeze.exit,
    remaining_closed: OWNER_ORDER.still_prohibits,
  };
}
