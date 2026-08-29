import { canonicalJson, digestText } from "@/lib/hash";
import type { OrganReceipt } from "@/lib/organs";

const STORAGE_KEY = "a11oy.organ-ledger.v1";

export interface OrganLedger {
  schema: "szl.organ-ledger/v1";
  entries: OrganReceipt[];
}

function empty(): OrganLedger {
  return { schema: "szl.organ-ledger/v1", entries: [] };
}

export function loadOrganLedger(): OrganLedger {
  if (typeof window === "undefined") return empty();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return empty();
    const parsed = JSON.parse(raw) as OrganLedger;
    if (!Array.isArray(parsed.entries)) return empty();
    return parsed;
  } catch {
    return empty();
  }
}

export function appendOrganReceipt(receipt: OrganReceipt): OrganLedger {
  const ledger = loadOrganLedger();
  if (ledger.entries.some((e) => e.hash === receipt.hash)) return ledger;
  ledger.entries.push(receipt);
  if (ledger.entries.length > 80) ledger.entries.splice(0, ledger.entries.length - 80);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ledger));
  }
  return ledger;
}

export async function verifyOrganReceipt(receipt: OrganReceipt) {
  const findings: string[] = [];
  if (receipt.schema !== "szl.organ-run/v1") findings.push("unknown organ schema");
  if (receipt.formula_grants_authority !== false) findings.push("formula must not grant authority");
  const { hash, ...rest } = receipt;
  const expected = await digestText(canonicalJson(rest));
  if (expected !== hash) findings.push("hash does not match canonical body");
  const inLedger = loadOrganLedger().entries.some((e) => e.hash === receipt.hash);
  return { ok: findings.length === 0, findings, inLedger };
}

export async function runOrganViaApi(id: string, prompt: string): Promise<OrganReceipt> {
  const response = await fetch(`/api/a11oy/v1/organs/${id}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `organ ${id} failed (${response.status})`);
  }
  const receipt = (await response.json()) as OrganReceipt;
  if (receipt?.schema !== "szl.organ-run/v1") throw new Error("organ API did not return a receipt");
  appendOrganReceipt(receipt);
  return receipt;
}
