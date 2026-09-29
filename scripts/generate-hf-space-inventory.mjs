#!/usr/bin/env node
/**
 * Generate src/lib/data/hf-space-inventory.json from the live public Hub.
 *
 *   node scripts/generate-hf-space-inventory.mjs            # write the file
 *   node scripts/generate-hf-space-inventory.mjs --check    # print, write nothing
 *
 * The read is unauthenticated, so it can only see public Spaces. A Space that
 * is absent from the result is NOT_OBSERVED: it may be private, or it may not
 * exist. The generator never guesses which, and it never mutates the Hub.
 * The org card Space SZLHOLDINGS/README is not returned by the list endpoint,
 * so it is read with its own public GET.
 */
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
export const OUTPUT = join(ROOT, "src", "lib", "data", "hf-space-inventory.json");
export const AUTHOR = "SZLHOLDINGS";
export const LIMIT = 1000;
export const LIST_ENDPOINT = `https://huggingface.co/api/spaces?author=${AUTHOR}&limit=${LIMIT}`;
export const ORG_CARD_ENDPOINT = `https://huggingface.co/api/spaces/${AUTHOR}/README`;
export const SCHEMA = "a11oy.factory.hf-space-inventory/v1";
const ID = new RegExp(`^${AUTHOR}/[A-Za-z0-9][A-Za-z0-9._-]{0,95}$`);

async function getJson(fetchImpl, url) {
  const response = await fetchImpl(url, {
    headers: { Accept: "application/json", "User-Agent": "a11oy-factory-hf-inventory/1" },
    redirect: "error",
  });
  return { status: response.status, body: response.ok ? await response.json() : null };
}

export async function buildInventory({ fetchImpl = fetch, now = () => new Date() } = {}) {
  const list = await getJson(fetchImpl, LIST_ENDPOINT);
  if (list.status !== 200) throw new Error(`Space list returned HTTP ${list.status}`);
  if (!Array.isArray(list.body)) throw new Error("Space list is not a JSON array");
  if (list.body.length >= LIMIT) throw new Error(`Space list reached the ${LIMIT}-row limit; paginate`);

  const ids = list.body.map((row) => {
    if (!row || typeof row.id !== "string" || !ID.test(row.id)) {
      throw new Error("Space list row without a valid SZLHOLDINGS id");
    }
    if (row.private === true) throw new Error(`unauthenticated list returned private Space ${row.id}`);
    return row.id;
  });
  if (new Set(ids).size !== ids.length) throw new Error("Space list contains duplicate ids");

  const orgCard = await getJson(fetchImpl, ORG_CARD_ENDPOINT);
  const orgCardPublic =
    orgCard.status === 200 && orgCard.body?.id === `${AUTHOR}/README` && orgCard.body?.private !== true;
  const all = orgCardPublic && !ids.includes(`${AUTHOR}/README`) ? [...ids, `${AUTHOR}/README`] : ids;

  return {
    schema: SCHEMA,
    observed_at: now().toISOString().replace(/\.\d{3}Z$/, "Z"),
    observation_mode: "UNAUTHENTICATED_PUBLIC_API",
    endpoints: { list: LIST_ENDPOINT, org_card: ORG_CARD_ENDPOINT },
    generator: "scripts/generate-hf-space-inventory.mjs",
    public_space_ids: [...all].sort(),
    limits: [
      "Only public Spaces are visible to this read. A Space absent here is NOT_OBSERVED: private, or not on the Hub.",
      "Presence here proves a public Hub repository at observed_at, not a RUNNING runtime.",
    ],
  };
}

export function serialize(inventory) {
  return `${JSON.stringify(inventory, null, 2)}\n`;
}

async function main(argv) {
  const inventory = await buildInventory();
  const text = serialize(inventory);
  if (argv.includes("--check")) {
    process.stdout.write(text);
    return;
  }
  writeFileSync(OUTPUT, text, "utf8");
  process.stdout.write(
    `wrote ${OUTPUT} (${inventory.public_space_ids.length} public Spaces at ${inventory.observed_at})\n`,
  );
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`generate-hf-space-inventory: ${error.message}\n`);
    process.exitCode = 1;
  });
}
