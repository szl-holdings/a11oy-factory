/**
 * Observed Hub state for configured Spaces, read from the generated inventory
 * (src/lib/data/hf-space-inventory.json, written by
 * scripts/generate-hf-space-inventory.mjs). No typed Space list decides what
 * exists on the Hub; the configuration only says what is planned.
 *
 * Dependency-free so node --experimental-strip-types can test it directly.
 */

export const HF_SPACE_INVENTORY_SCHEMA = "a11oy.factory.hf-space-inventory/v1";

export interface HfSpaceInventory {
  schema: typeof HF_SPACE_INVENTORY_SCHEMA;
  observed_at: string;
  observation_mode: "UNAUTHENTICATED_PUBLIC_API";
  endpoints: { list: string; org_card: string };
  generator: string;
  public_space_ids: string[];
  limits: string[];
}

export type HubObservationState = "PUBLIC_OBSERVED" | "NOT_OBSERVED";

export interface HubObservation {
  state: HubObservationState;
  observed_at: string;
  url: string | null;
  note: string;
}

const SPACE_ID = /^SZLHOLDINGS\/[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/;
const UTC_SECOND = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;

function fail(reason: string): never {
  throw new Error(`hf-space-inventory: ${reason}`);
}

/** Fail closed on anything the generator would not have written. */
export function validateInventory(value: unknown): HfSpaceInventory {
  if (!value || typeof value !== "object") fail("not an object");
  const inventory = value as Partial<HfSpaceInventory>;
  if (inventory.schema !== HF_SPACE_INVENTORY_SCHEMA) fail("unexpected schema");
  if (inventory.observation_mode !== "UNAUTHENTICATED_PUBLIC_API") fail("unexpected observation mode");
  if (typeof inventory.observed_at !== "string" || !UTC_SECOND.test(inventory.observed_at)) {
    fail("observed_at must be a UTC second timestamp");
  }
  if (inventory.generator !== "scripts/generate-hf-space-inventory.mjs") fail("unexpected generator");
  const ids = inventory.public_space_ids;
  if (!Array.isArray(ids) || ids.length === 0) fail("public_space_ids must be a non-empty array");
  if (!ids.every((id) => typeof id === "string" && SPACE_ID.test(id))) fail("invalid Space id");
  const sorted = [...ids].sort();
  if (new Set(ids).size !== ids.length || sorted.some((id, index) => id !== ids[index])) {
    fail("public_space_ids must be sorted and unique");
  }
  return inventory as HfSpaceInventory;
}

export function observeSpace(inventory: HfSpaceInventory, id: string): HubObservation {
  if (inventory.public_space_ids.includes(id)) {
    return {
      state: "PUBLIC_OBSERVED",
      observed_at: inventory.observed_at,
      url: `https://huggingface.co/spaces/${id}`,
      note: "Public Hub repository observed; not a runtime-health claim.",
    };
  }
  return {
    state: "NOT_OBSERVED",
    observed_at: inventory.observed_at,
    url: null,
    note: "Not in the unauthenticated public Space list: private, or not on the Hub.",
  };
}

export function inventorySummary(inventory: HfSpaceInventory) {
  return {
    public_spaces_observed: inventory.public_space_ids.length,
    observed_at: inventory.observed_at,
    observation_mode: inventory.observation_mode,
    endpoint: inventory.endpoints.list,
    generator: inventory.generator,
  };
}
