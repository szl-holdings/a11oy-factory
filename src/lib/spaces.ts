import { cellOverlay, OWNER_ORDER } from "@/lib/admission";
import { profile } from "@/lib/data/registry";

export type SpaceVisibility = "public" | "protected" | "private";
export type SpacePublish = "LIVE" | "PREPARED_NOT_LIVE" | "KEEP" | "MERGE" | "DO_NOT_PUBLISH" | "PUBLISHED_PRIVATE";

export interface SpaceConfig {
  id: string;
  title: string;
  role: string;
  visibility: SpaceVisibility;
  sdk: "docker" | "static" | "gradio" | "streamlit";
  app_port: number | null;
  hardware: "cpu-basic";
  license: "apache-2.0";
  publish: SpacePublish;
  canonical: boolean;
  vertical_id: string | null;
  source: string;
  recommended_action: string;
  card: string;
  limitations: string[];
}

const SHARED_LIMITS = [
  "Formulas never grant authority.",
  "This configuration does not mutate Hub until HF_TOKEN is present.",
  "a-11-oy.com is not certified by a Space card.",
];

export const CANONICAL_PUBLIC_SIX = [
  "SZLHOLDINGS/README",
  "SZLHOLDINGS/a11oy",
  "SZLHOLDINGS/killinchu",
  "SZLHOLDINGS/lyte-services",
  "SZLHOLDINGS/szl-model-inference-lab",
  "SZLHOLDINGS/evidence-studio",
] as const;

export const SPACE_CONFIGS: SpaceConfig[] = [
  {
    id: "SZLHOLDINGS/README",
    title: "SZL Holdings",
    role: "Organization front door",
    visibility: "public",
    sdk: "static",
    app_port: null,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "KEEP",
    canonical: true,
    vertical_id: null,
    source: "https://huggingface.co/spaces/SZLHOLDINGS/README",
    recommended_action: "KEEP_CANONICAL",
    card: "Keep the org card. Do not turn it into a second product.",
    limitations: SHARED_LIMITS,
  },
  {
    id: "SZLHOLDINGS/a11oy",
    title: "A11oy",
    role: "Core product demonstration",
    visibility: "public",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "KEEP",
    canonical: true,
    vertical_id: null,
    source: "https://huggingface.co/spaces/SZLHOLDINGS/a11oy",
    recommended_action: "KEEP_CANONICAL",
    card: "Flagship Space. Factory binds here. Not replaced by a11oy-factory.",
    limitations: SHARED_LIMITS,
  },
  {
    id: "SZLHOLDINGS/killinchu",
    title: "Killinchu",
    role: "Bounded public synthetic reference",
    visibility: "public",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "KEEP",
    canonical: true,
    vertical_id: "killinchu",
    source: "https://huggingface.co/spaces/SZLHOLDINGS/killinchu",
    recommended_action: "REPAIR_AND_KEEP_CANONICAL",
    card: "Public only as a simulated proposal system. No physical effector.",
    limitations: [
      ...SHARED_LIMITS,
      "Weapon command, targeting, and effector integration remain prohibited.",
    ],
  },
  {
    id: "SZLHOLDINGS/lyte-services",
    title: "Lyte Services",
    role: "Admitted protected design-partner cell",
    visibility: "protected",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "PREPARED_NOT_LIVE",
    canonical: true,
    vertical_id: "lyte-services",
    source: "https://huggingface.co/spaces/SZLHOLDINGS/lyte-services",
    recommended_action: "ADMITTED_PROTECTED_PILOT",
    card: "Owner-admitted. Protected, not public launch. Same factory image + Lyte manifest.",
    limitations: [
      ...SHARED_LIMITS,
      "Public launch stays blocked until measured pilot evidence.",
    ],
  },
  {
    id: "SZLHOLDINGS/szl-model-inference-lab",
    title: "Model inference lab",
    role: "Canonical inference laboratory",
    visibility: "public",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "KEEP",
    canonical: true,
    vertical_id: null,
    source: "https://huggingface.co/spaces/SZLHOLDINGS/szl-model-inference-lab",
    recommended_action: "KEEP_CANONICAL",
    card: "Keep as the public inference lab. Not a vertical cell.",
    limitations: SHARED_LIMITS,
  },
  {
    id: "SZLHOLDINGS/evidence-studio",
    title: "Evidence Studio",
    role: "Canonical merge sink for holographic / receipt Spaces",
    visibility: "public",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "PREPARED_NOT_LIVE",
    canonical: true,
    vertical_id: null,
    source: "https://huggingface.co/spaces/SZLHOLDINGS/evidence-studio",
    recommended_action: "PREPARE_MERGE_SINK",
    card: "Prepared. Do not publish until holographic Spaces are merged into this one writer.",
    limitations: [
      ...SHARED_LIMITS,
      "Creating this Space on Hub is blocked until HF_TOKEN exists.",
    ],
  },
  {
    id: "SZLHOLDINGS/a11oy-factory",
    title: "A11oy Factory",
    role: "Vertical factory control plane",
    visibility: "protected",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "PUBLISHED_PRIVATE",
    canonical: false,
    vertical_id: null,
    source: OWNER_ORDER.github.url,
    recommended_action: "BIND_AS_A11OY_PACKAGE",
    card: "Private Docker Space published via szl-experiments sibling publisher. Not a second flagship. Not a seventh public Space.",
    limitations: [
      ...SHARED_LIMITS,
      "Must remain protected. Do not pin on the org front door.",
    ],
  },
  {
    id: "SZLHOLDINGS/aegis-assurance",
    title: "Aegis Assurance",
    role: "Next vertical after Lyte traction",
    visibility: "protected",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "DO_NOT_PUBLISH",
    canonical: false,
    vertical_id: "aegis-assurance",
    source: "https://huggingface.co/spaces/SZLHOLDINGS/aegis-assurance",
    recommended_action: "HOLD_UNTIL_LYTE_TRACTION",
    card: "Same factory image. Do not publish before Lyte traction and the security gate.",
    limitations: SHARED_LIMITS,
  },
  {
    id: "SZLHOLDINGS/vessels-assurance",
    title: "Vessels Assurance",
    role: "Partner and data gated specialty",
    visibility: "private",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "DO_NOT_PUBLISH",
    canonical: false,
    vertical_id: "vessels-assurance",
    source: "https://huggingface.co/spaces/SZLHOLDINGS/vessels-assurance",
    recommended_action: "HOLD_PRIVATE",
    card: "Private until licensed data and a maritime partner exist.",
    limitations: SHARED_LIMITS,
  },
  {
    id: "SZLHOLDINGS/terra-assurance",
    title: "Terra Assurance",
    role: "Private incubator",
    visibility: "private",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "DO_NOT_PUBLISH",
    canonical: false,
    vertical_id: "terra-assurance",
    source: "https://huggingface.co/spaces/SZLHOLDINGS/terra-assurance",
    recommended_action: "HOLD_PRIVATE",
    card: "Private until data rights and a design partner exist.",
    limitations: SHARED_LIMITS,
  },
  {
    id: "SZLHOLDINGS/counsel-assurance",
    title: "Counsel Assurance",
    role: "Qualified legal partner gate",
    visibility: "private",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "DO_NOT_PUBLISH",
    canonical: false,
    vertical_id: "counsel-assurance",
    source: "https://huggingface.co/spaces/SZLHOLDINGS/counsel-assurance",
    recommended_action: "HOLD_PRIVATE",
    card: "Private. No public legal advice. No automatic filing.",
    limitations: SHARED_LIMITS,
  },
  {
    id: "SZLHOLDINGS/david-leads",
    title: "Insurance Assurance",
    role: "Consent-bound reference vertical",
    visibility: "protected",
    sdk: "docker",
    app_port: 7860,
    hardware: "cpu-basic",
    license: "apache-2.0",
    publish: "KEEP",
    canonical: false,
    vertical_id: "insurance-assurance",
    source: "https://huggingface.co/spaces/SZLHOLDINGS/david-leads",
    recommended_action: "REFACTOR_FROM_SHARED_FACTORY",
    card: "Keep the existing Space as a module. Do not promote David Leads as a flagship.",
    limitations: SHARED_LIMITS,
  },
];

export function spaceYaml(space: SpaceConfig): string {
  const lines = [
    "---",
    `title: ${space.title}`,
    "emoji: ⚖️",
    "colorFrom: yellow",
    "colorTo: gray",
    `sdk: ${space.sdk}`,
  ];
  if (space.app_port) lines.push(`app_port: ${space.app_port}`);
  lines.push(
    "pinned: false",
    `license: ${space.license}`,
    "suggested_hardware: cpu-basic",
    `short_description: ${space.card}`,
    "---",
    "",
    `# ${space.title}`,
    "",
    space.card,
    "",
    `- Visibility: **${space.visibility}**`,
    `- Publish: **${space.publish}**`,
    `- Action: **${space.recommended_action}**`,
    `- Canonical six: ${space.canonical ? "yes" : "no"}`,
    "",
    ...space.limitations.map((item) => `- ${item}`),
    "",
  );
  return lines.join("\n");
}

export function spacePlan() {
  const inventory = profile.hugging_face_assets.filter((a) => a.category === "space");
  const configuredIds = new Set(SPACE_CONFIGS.map((s) => s.id));
  const merge = inventory.filter(
    (a) => !configuredIds.has(a.asset_id) && a.recommended_action.startsWith("MERGE"),
  );
  const live_org_observation = {
    captured_packet6: profile.counts.hf_spaces,
    live_org_page_2026_08_29: 36,
    drift_note:
      "Packet 6 counted 27 Spaces. The live org page now lists 36. This plan does not scrape Hub and does not mutate Hub.",
  };

  return {
    schema: "szl.space-release-plan/v1" as const,
    owner_order_id: OWNER_ORDER.order_id,
    factory_repo: OWNER_ORDER.github.factory_repo,
    huggingface_token: "PRESENT_ON_SZL_EXPERIMENTS",
    hub_mutation: "published-private-via-szl-experiments",
    canonical_six: CANONICAL_PUBLIC_SIX,
    configured: SPACE_CONFIGS.map((space) => ({
      ...space,
      overlay: space.vertical_id ? cellOverlay(space.vertical_id) : null,
      yaml: spaceYaml(space),
    })),
    merge_into_evidence_studio: merge.map((a) => a.asset_id),
    inventory_count: inventory.length,
    live_org_observation,
    truth:
      "Factory Space SZLHOLDINGS/a11oy-factory is published private via szl-experiments. Lyte is protected, not public. a11oy-factory is a package bind, not a seventh public Space. Docker metadata is fetching — not a production certificate.",
  };
}
