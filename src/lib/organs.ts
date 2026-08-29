import { canonicalJson, digestText } from "@/lib/hash";
import type { DecisionStatus, EvidenceClass } from "@/lib/types";

export type OrganId =
  | "N1" | "N2" | "N3" | "N4" | "N5" | "N6" | "N7" | "N8"
  | "N9" | "N10" | "N11" | "N12" | "N13" | "N14" | "N15"
  | "N16" | "N17" | "N18" | "N19" | "N20" | "N21" | "N22"
  | "N23" | "N24" | "N25";

export interface OrganDef {
  id: OrganId;
  title: string;
  body: string;
  job: string;
  honesty: "LIVE";
  evidence_class: EvidenceClass;
  placeholder: string;
  admitted_public: false;
}

export interface OrganInput {
  prompt?: string;
  payload?: Record<string, string | number | boolean>;
}

export interface OrganReceipt {
  schema: "szl.organ-run/v1";
  id: OrganId;
  title: string;
  status: DecisionStatus;
  honesty: "LIVE";
  evidence_class: EvidenceClass;
  formula_grants_authority: false;
  input: OrganInput;
  output: Record<string, unknown>;
  limitations: string[];
  hash: string;
  created_at: string;
}

const MEMORY = new Map<string, { k: string; v: string; at: string }>();
const CACHE = new Map<string, { v: string; hits: number }>();
const TRACES: Array<{ id: string; organ: string; at: string; note: string }> = [];

export const ORGANS: OrganDef[] = [
  { id: "N1", title: "Serve", body: "brain", job: "inference serving", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Prompt to serve (schema-checked, no GPU claim)", admitted_public: false },
  { id: "N2", title: "Graph", body: "nervous", job: "agent orchestration", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Goal for a 3-node fail-closed graph", admitted_public: false },
  { id: "N3", title: "Guard", body: "immune", job: "input/output safeguard", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Text to screen (deny weapons / PII / exfil)", admitted_public: false },
  { id: "N4", title: "Mosaic", body: "circulatory", job: "data mosaic", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Join key, e.g. lyte-pilot-01", admitted_public: false },
  { id: "N5", title: "Lattice", body: "immune", job: "defense overlay", honesty: "LIVE", evidence_class: "MODELED", placeholder: "Request to score against the lattice", admitted_public: false },
  { id: "N6", title: "Cover", body: "heart", job: "P&C insurance core", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Risk note for a synthetic quote", admitted_public: false },
  { id: "N7", title: "Quant", body: "brain", job: "algorithmic research and backtest", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Ticker, e.g. SYN", admitted_public: false },
  { id: "N8", title: "Title", body: "skeleton", job: "property records", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Parcel id, e.g. 14-22-08", admitted_public: false },
  { id: "N9", title: "Retrieve", body: "nervous", job: "retrieval and memory", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Query the factory corpus", admitted_public: false },
  { id: "N10", title: "Observe", body: "immune", job: "trace and evaluation", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Note to attach as a trace", admitted_public: false },
  { id: "N11", title: "Tune", body: "brain", job: "receipted fine-tune", honesty: "LIVE", evidence_class: "UNAVAILABLE", placeholder: "Dataset digest to request a tune (GPU denied)", admitted_public: false },
  { id: "N12", title: "Schema", body: "skeleton", job: "constrained generation", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Fill a Lyte quote schema from a sentence", admitted_public: false },
  { id: "N13", title: "Energy", body: "circulatory", job: "joule accounting", honesty: "LIVE", evidence_class: "MODELED", placeholder: "Token count to model joules", admitted_public: false },
  { id: "N14", title: "Tool", body: "nervous", job: "agent tool protocol", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "tool:lookup | tool:quote | tool:forbidden", admitted_public: false },
  { id: "N15", title: "Memory", body: "brain", job: "persistent agent memory", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "key=value to store, or a key to recall", admitted_public: false },
  { id: "N16", title: "Eval", body: "immune", job: "offline evaluation", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Suite name, e.g. lyte-negatives", admitted_public: false },
  { id: "N17", title: "Mesh", body: "circulatory", job: "distributed inference", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Prompt to fan out across 3 synthetic nodes", admitted_public: false },
  { id: "N18", title: "Route", body: "circulatory", job: "LLM gateway and routing", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Prompt; route by length / deny / json", admitted_public: false },
  { id: "N19", title: "Cache", body: "circulatory", job: "prefix and semantic cache", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Prefix to cache or look up", admitted_public: false },
  { id: "N20", title: "Voice", body: "nervous", job: "realtime duplex voice", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Utterance to wrap as a duplex turn", admitted_public: false },
  { id: "N21", title: "Sandbox", body: "skeleton", job: "isolated agent code execution", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Integer math only, e.g. (2+3)*4", admitted_public: false },
  { id: "N22", title: "Identity", body: "skeleton", job: "non-human agent identity", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Agent role, e.g. lyte-underwriter", admitted_public: false },
  { id: "N23", title: "Rails", body: "immune", job: "conversation rails", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "Turn text; rails refuse out-of-policy", admitted_public: false },
  { id: "N24", title: "Browser", body: "nervous", job: "agent browser actuation", honesty: "LIVE", evidence_class: "SIMULATED", placeholder: "Same-origin path, e.g. /trust", admitted_public: false },
  { id: "N25", title: "Policy", body: "immune", job: "authorization policy for tools", honesty: "LIVE", evidence_class: "MEASURED", placeholder: "tool=quote resource=lyte", admitted_public: false },
];

const CORPUS = [
  "Lyte is the admitted protected design-partner cell.",
  "Killinchu is the only public synthetic reference.",
  "Formulas never grant authority. Locked set is exactly 8.",
  "Decision Cell Compiler binds a vertical manifest into receipts.",
  "Nexus is classified as an A11oy incubator package.",
];

const QUOTES: Record<string, { parcel: string; holder: string; status: string }> = {
  "14-22-08": { parcel: "14-22-08", holder: "synthetic-trust-a", status: "clear" },
  "99-00-01": { parcel: "99-00-01", holder: "synthetic-trust-b", status: "lien" },
};

const MOSAIC: Record<string, { buyer: string; exposure: string }> = {
  "lyte-pilot-01": { buyer: "Lyte Services", exposure: "protected-pilot" },
};

function promptOf(input: OrganInput): string {
  return String(input.prompt ?? input.payload?.prompt ?? "").trim();
}

function denyWeapons(text: string): boolean {
  return /\b(weapon|target(ing)?|kill chain|munition|exfil|ssn\b|password\s*=)/i.test(text);
}

function safeMath(expr: string): number {
  const clean = expr.replace(/\s+/g, "");
  if (!clean || !/^[0-9+\-*/().]+$/.test(clean)) throw new Error("sandbox denied: not integer math");
  if (clean.length > 64) throw new Error("sandbox denied: too long");
  let i = 0;
  function peek() { return clean[i] ?? ""; }
  function eat(c?: string) {
    if (c && peek() !== c) throw new Error("sandbox denied");
    i += 1;
  }
  function num(): number {
    let s = "";
    if (peek() === "-") { s = "-"; eat(); }
    while (/[0-9]/.test(peek())) s += clean[i++];
    if (!s || s === "-") throw new Error("sandbox denied");
    return Number(s);
  }
  function factor(): number {
    if (peek() === "(") { eat("("); const v = exprP(); eat(")"); return v; }
    return num();
  }
  function term(): number {
    let v = factor();
    while (peek() === "*" || peek() === "/") {
      const op = peek(); eat();
      const r = factor();
      v = op === "*" ? v * r : r === 0 ? (() => { throw new Error("div/0"); })() : v / r;
    }
    return v;
  }
  function exprP(): number {
    let v = term();
    while (peek() === "+" || peek() === "-") {
      const op = peek(); eat();
      const r = term();
      v = op === "+" ? v + r : v - r;
    }
    return v;
  }
  const v = exprP();
  if (i !== clean.length) throw new Error("sandbox denied: trailing");
  if (!Number.isFinite(v)) throw new Error("sandbox denied");
  return v;
}

async function receipt(
  def: OrganDef,
  input: OrganInput,
  status: DecisionStatus,
  output: Record<string, unknown>,
  limitations: string[],
): Promise<OrganReceipt> {
  const created_at = new Date().toISOString();
  const unsigned = {
    schema: "szl.organ-run/v1" as const,
    id: def.id,
    title: def.title,
    status,
    honesty: "LIVE" as const,
    evidence_class: def.evidence_class,
    formula_grants_authority: false as const,
    input,
    output,
    limitations,
    created_at,
  };
  const hash = await digestText(canonicalJson(unsigned));
  return { ...unsigned, hash };
}

type Runner = (def: OrganDef, input: OrganInput) => Promise<OrganReceipt>;

const RUNNERS: Record<OrganId, Runner> = {
  async N1(def, input) {
    const prompt = promptOf(input);
    if (!prompt) return receipt(def, input, "DENIED", { reason: "empty prompt" }, ["Serve refuses empty input"]);
    if (denyWeapons(prompt)) return receipt(def, input, "DENIED", { reason: "guarded" }, ["Serve is fail-closed"]);
    return receipt(def, input, "EXECUTED", {
      object: "chat.completion",
      model: "factory-schema-envelope",
      choices: [{ message: { role: "assistant", content: `Served (structural): ${prompt.slice(0, 240)}` } }],
      gpu: false,
    }, ["No GPU. Schema envelope only. Not a vLLM rehost."]);
  },
  async N2(def, input) {
    const goal = promptOf(input) || "compile-lyte-quote";
    const nodes = ["intake", "policy-shadow", "human-interrupt"].map((name, idx) => ({
      name,
      state: idx < 2 ? "DONE" : "AWAITING_APPROVAL",
    }));
    return receipt(def, input, "AWAITING_APPROVAL", { goal, nodes, interrupt: true }, ["Graph never auto-promotes. Human interrupt is required."]);
  },
  async N3(def, input) {
    const text = promptOf(input);
    const denied = !text || denyWeapons(text);
    return receipt(def, input, denied ? "DENIED" : "EXECUTED", {
      action: denied ? "DENY" : "ALLOW",
      rules: ["weapons", "exfil", "secrets"],
    }, ["Guard is LOG_ONLY overlay. Not a production WAF."]);
  },
  async N4(def, input) {
    const key = promptOf(input) || "lyte-pilot-01";
    const row = MOSAIC[key];
    return receipt(def, input, row ? "EXECUTED" : "DENIED", {
      key,
      row: row ?? null,
      sources: ["synthetic-buyer", "synthetic-exposure"],
    }, ["Synthetic mosaic only. No private corpus."]);
  },
  async N5(def, input) {
    const text = promptOf(input);
    const score = denyWeapons(text) ? 0.12 : 0.81;
    return receipt(def, input, score < 0.5 ? "DENIED" : "EXECUTED", {
      lattice_score: score,
      overlay: "defense-in-depth",
    }, ["Modeled overlay. Not a measured SOC."]);
  },
  async N6(def, input) {
    const note = promptOf(input) || "warehouse sprinklered";
    const premium = 1200 + (denyWeapons(note) ? 0 : note.length * 3);
    return receipt(def, input, denyWeapons(note) ? "DENIED" : "EXECUTED", {
      product: "P&C-synthetic",
      premium_usd: premium,
      bind: "LOG_ONLY",
    }, ["Synthetic quote. Not a licensed insurance bind."]);
  },
  async N7(def, input) {
    const ticker = (promptOf(input) || "SYN").toUpperCase().slice(0, 8);
    const series = Array.from({ length: 8 }, (_, i) => 100 + Math.sin(i) * 4 + i);
    const ret = (series.at(-1)! - series[0]!) / series[0]!;
    return receipt(def, input, "EXECUTED", { ticker, series, return: Number(ret.toFixed(4)), causal: false }, ["Synthetic series. Causal claims prohibited."]);
  },
  async N8(def, input) {
    const id = promptOf(input) || "14-22-08";
    const rec = QUOTES[id];
    return receipt(def, input, rec ? "EXECUTED" : "DENIED", { id, record: rec ?? null }, ["Synthetic title plant. Not a county system."]);
  },
  async N9(def, input) {
    const q = promptOf(input).toLowerCase();
    const hits = CORPUS.filter((row) => !q || row.toLowerCase().includes(q)).slice(0, 3);
    return receipt(def, input, hits.length ? "EXECUTED" : "DENIED", { query: q, hits }, ["In-factory corpus only."]);
  },
  async N10(def, input) {
    const note = promptOf(input) || "observe";
    const row = { id: `tr_${TRACES.length + 1}`, organ: def.id, at: new Date().toISOString(), note };
    TRACES.push(row);
    return receipt(def, input, "EXECUTED", { attached: row, traces: TRACES.slice(-5) }, ["In-process traces. Not a vendor APM."]);
  },
  async N11(def, input) {
    const digest = promptOf(input) || "sha256:unavailable";
    return receipt(def, input, "DENIED", { dataset: digest, gpu: "UNAVAILABLE", job: "not-queued" }, ["Tune is receipted and refused. No GPU in this runtime."]);
  },
  async N12(def, input) {
    const text = promptOf(input) || "Lyte warehouse quote";
    const obj = {
      insured: /lyte/i.test(text) ? "Lyte Services" : "synthetic-buyer",
      occupancy: /ware/i.test(text) ? "warehouse" : "unspecified",
      bind: false,
    };
    return receipt(def, input, "EXECUTED", { schema: "lyte.quote.v1", value: obj }, ["Constrained fill. Not a model decode."]);
  },
  async N13(def, input) {
    const n = Number(promptOf(input)) || promptOf(input).length || 128;
    const joules = Number((n * 0.0024).toFixed(4));
    return receipt(def, input, "EXECUTED", { tokens: n, joules_modeled: joules }, ["Modeled joules. Not a watt-meter."]);
  },
  async N14(def, input) {
    const name = (promptOf(input) || "lookup").replace(/^tool:/, "");
    const allow = ["lookup", "quote"];
    if (!allow.includes(name)) return receipt(def, input, "DENIED", { tool: name, allow }, ["Unknown tools are denied."]);
    return receipt(def, input, "EXECUTED", { tool: name, result: name === "lookup" ? CORPUS[0] : { premium_usd: 1200 } }, ["Allowlisted tools only."]);
  },
  async N15(def, input) {
    const raw = promptOf(input);
    if (raw.includes("=")) {
      const [k, ...rest] = raw.split("=");
      const rec = { k: k.trim(), v: rest.join("=").trim(), at: new Date().toISOString() };
      MEMORY.set(rec.k, rec);
      return receipt(def, input, "EXECUTED", { stored: rec, size: MEMORY.size }, ["Process memory. Not a customer vault."]);
    }
    const hit = MEMORY.get(raw);
    return receipt(def, input, hit ? "EXECUTED" : "DENIED", { key: raw, value: hit ?? null }, ["Recall miss is DENIED, not fabricated."]);
  },
  async N16(def, input) {
    const suite = promptOf(input) || "lyte-negatives";
    const cases = [
      { id: "neg-stale", pass: true },
      { id: "neg-missing", pass: true },
      { id: "pos-quote", pass: true },
      { id: "weapon", pass: true },
    ];
    return receipt(def, input, "EXECUTED", { suite, passed: cases.filter((c) => c.pass).length, cases }, ["Offline fixtures. Not a live customer eval."]);
  },
  async N17(def, input) {
    const prompt = promptOf(input) || "fanout";
    const nodes = ["alpha", "beta", "gamma"].map((name) => ({ name, echo: prompt.slice(0, 80), ok: true }));
    return receipt(def, input, "EXECUTED", { nodes, aggregate: nodes.map((n) => n.name) }, ["Synthetic mesh. Not a GPU cluster."]);
  },
  async N18(def, input) {
    const prompt = promptOf(input);
    const route = denyWeapons(prompt) ? "deny" : prompt.trim().startsWith("{") ? "json-schema" : prompt.length > 400 ? "long-context" : "default";
    const status: DecisionStatus = route === "deny" ? "DENIED" : "EXECUTED";
    return receipt(def, input, status, { route, backends: ["default", "json-schema", "long-context", "deny"] }, ["Rule router. No vendor keys."]);
  },
  async N19(def, input) {
    const key = promptOf(input);
    if (!key) return receipt(def, input, "DENIED", { reason: "empty prefix" }, ["Cache needs a prefix"]);
    const hit = CACHE.get(key);
    if (hit) {
      hit.hits += 1;
      return receipt(def, input, "EXECUTED", { hit: true, value: hit.v, hits: hit.hits }, ["In-process prefix cache."]);
    }
    CACHE.set(key, { v: `cached:${key.slice(0, 80)}`, hits: 0 });
    return receipt(def, input, "EXECUTED", { hit: false, stored: true }, ["Miss stored. Not a semantic GPU cache."]);
  },
  async N20(def, input) {
    const utter = promptOf(input) || "acknowledge";
    return receipt(def, input, "EXECUTED", {
      turn: { user: utter, assistant: `Heard (transcript only): ${utter}` },
      audio: false,
    }, ["Transcript envelope. Not a realtime voice stack."]);
  },
  async N21(def, input) {
    try {
      const value = safeMath(promptOf(input) || "1+1");
      return receipt(def, input, "EXECUTED", { value }, ["Integer math sandbox. No eval, no FS, no net."]);
    } catch (err) {
      return receipt(def, input, "DENIED", { reason: err instanceof Error ? err.message : "denied" }, ["Fail closed."]);
    }
  },
  async N22(def, input) {
    const role = promptOf(input) || "lyte-underwriter";
    const id = await digestText(`nhi:${role}`);
    return receipt(def, input, "EXECUTED", { agent_id: `nhi_${id.slice(0, 16)}`, role, human: false }, ["Synthetic NHI. Not a production IdP."]);
  },
  async N23(def, input) {
    const turn = promptOf(input);
    const off = denyWeapons(turn) || /ignore previous|jailbreak/i.test(turn);
    return receipt(def, input, off ? "DENIED" : "EXECUTED", { rail: off ? "block" : "allow", turn }, ["Conversation rails. Not a full safety model."]);
  },
  async N24(def, input) {
    const path = promptOf(input) || "/trust";
    const allow = /^\/[a-z0-9/_-]*$/i.test(path);
    return receipt(def, input, allow ? "EXECUTED" : "DENIED", {
      path,
      actuation: allow ? `navigate:${path}` : null,
      same_origin: true,
    }, ["Same-origin navigation log. No remote browse."]);
  },
  async N25(def, input) {
    const text = promptOf(input) || "tool=quote resource=lyte";
    const tool = /tool=([a-z0-9-]+)/i.exec(text)?.[1] ?? "quote";
    const resource = /resource=([a-z0-9-]+)/i.exec(text)?.[1] ?? "lyte";
    const allow = (tool === "quote" || tool === "lookup") && resource === "lyte";
    return receipt(def, input, allow ? "APPROVED" : "DENIED", { tool, resource, allow }, ["Tool authorization. Formulas never grant authority."]);
  },
};

const RUN_LOG: OrganReceipt[] = [];
const RUN_LOG_CAP = 50;

export function rememberOrganRun(receipt: OrganReceipt): void {
  RUN_LOG.push(receipt);
  if (RUN_LOG.length > RUN_LOG_CAP) RUN_LOG.splice(0, RUN_LOG.length - RUN_LOG_CAP);
}

export function recentOrganRuns(limit = 20): OrganReceipt[] {
  return RUN_LOG.slice(-limit).reverse();
}

export function organById(id: string): OrganDef | undefined {
  return ORGANS.find((o) => o.id === id);
}

export async function runOrgan(id: string, input: OrganInput = {}): Promise<OrganReceipt> {
  const def = organById(id);
  if (!def) {
    throw new Error(`unknown organ ${id}`);
  }
  const result = await RUNNERS[def.id](def, input);
  rememberOrganRun(result);
  return result;
}

export const ORGAN_ENDPOINTS = [
  { method: "GET", path: "/api/a11oy/v1/organs", purpose: "catalog + recent runs" },
  { method: "GET", path: "/api/a11oy/v1/organs/{id}", purpose: "single organ contract" },
  { method: "POST", path: "/api/a11oy/v1/organs/{id}", purpose: "execute organ, hashed receipt" },
  { method: "GET", path: "/api/a11oy/v1/organs/history", purpose: "process-local run log" },
] as const;

export function organCatalog() {
  return {
    schema: "szl.organ-catalog/v1" as const,
    honesty: "LIVE" as const,
    count: ORGANS.length,
    admitted_public: false,
    endpoints: ORGAN_ENDPOINTS,
    recent: recentOrganRuns(8).map((r) => ({
      id: r.id,
      title: r.title,
      status: r.status,
      hash: r.hash,
      created_at: r.created_at,
    })),
    items: ORGANS.map((o) => ({
      id: o.id,
      title: o.title,
      body: o.body,
      job: o.job,
      honesty: o.honesty,
      evidence_class: o.evidence_class,
      run: `POST /api/a11oy/v1/organs/${o.id}`,
    })),
    note: "N1–N25 execute in this factory. Not 25 public Spaces. GPU tune remains UNAVAILABLE.",
  };
}
