"""Fail-closed organs. Roadmaps STARTED. Compile still BLOCKED. Never LIVE.

We searched the 2026 jobs (vLLM serve, MCP tools, LiteLLM gateway, SPIFFE NHI,
NeMo rails, Playwright browser, Cedar policy) and took the job, not the code.
Each organ runs a receipted refuse. STARTED ≠ admitted. STARTED ≠ LIVE.
Energy stays UNAVAILABLE. Λ stays Conjecture 1. Hash is UNSIGNED-honest.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from .cells import FRONTIERS, LYTE, resolve_cell
from .compiler import compile_cell

PHASE_ADMITTED = "ADMITTED"
PHASE_STARTED = "STARTED"
ALLOWED_TOOLS = frozenset({"receipt.write"})
GUARD_TRIPS = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "jailbreak",
    "ssn",
    "social security",
)
RAIL_TOPICS = frozenset({"compile", "search", "receipt", "health", "lyte", "roadmap"})
SCHEMA_TYPES = {"object": dict, "string": str, "number": (int, float), "boolean": bool, "array": list}


def _sha256(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def _base(cell_id: str, payload: dict) -> dict:
    rec = compile_cell(cell_id)
    cell = resolve_cell(cell_id)
    return {
        "ok": False,
        "halt": True,
        "phase": PHASE_ADMITTED if rec.decision == "ALLOW" else PHASE_STARTED,
        "decision": rec.decision,
        "honesty": rec.honesty_tier,
        "cell": rec.cell,
        "organ": rec.organ,
        "title": cell.title if cell else rec.cell,
        "admitted": bool(cell and cell.admitted),
        "live": False,
        "lambda_status": "Conjecture 1",
        "energy": None,
        "signer": "UNSIGNED-honest",
        "payload_digest": _sha256({"payload": payload, "cell": rec.cell}),
        "compile_hash": rec.hash,
    }


def _schema_check(schema: Any, value: Any) -> tuple[bool, str]:
    if not isinstance(schema, dict) or not schema:
        return False, "schema required. Fail closed."
    want = schema.get("type")
    py = SCHEMA_TYPES.get(want) if isinstance(want, str) else None
    if py is None:
        return False, f"unsupported schema type {want!r}. Fail closed."
    if not isinstance(value, py) or (want == "number" and isinstance(value, bool)):
        return False, f"value is not {want}. Fail closed."
    if want == "object":
        required = schema.get("required") or []
        if not isinstance(required, list):
            return False, "required must be a list. Fail closed."
        missing = [k for k in required if not isinstance(k, str) or k not in value]
        if missing:
            return False, f"missing required {missing}. Fail closed."
    return True, "types hold. Not constrained decode. Not Outlines. Not LIVE."


def _serve(payload: dict) -> dict:
    return {
        "error": {
            "message": "No weights on this organ. Fail closed.",
            "type": "blocked",
            "code": "no_weights",
        },
        "choices": [],
        "note": "OpenAI-shaped refuse. Schema outside the weights. Not a vLLM/SGLang/Ollama/TRT-LLM rehost.",
    }


def _graph(payload: dict) -> dict:
    edge = str(payload.get("edge") or payload.get("node") or "")
    return {
        "edge": edge or None,
        "reason": "Unknown or unreceipted edge. SENTRA fail closed. Not a LangGraph rehost.",
    }


def _guard(payload: dict) -> dict:
    text = str(payload.get("text") or payload.get("prompt") or payload.get("output") or "").lower()
    hits = [t for t in GUARD_TRIPS if t in text]
    halt = (not text) or bool(hits)
    return {
        "halt": halt,
        "hits": hits,
        "note": "SENTRA tripwire taxonomy. Not Llama Guard weights. Not Purple Llama.",
    }


def _mosaic(payload: dict) -> dict:
    return {"reason": "No train. Lineage only. Not a MosaicML/Databricks rehost."}


def _lattice(payload: dict) -> dict:
    return {"reason": "Overlay bind is not admitted. Defense only. Hub vertical may be LIVE; this bind is not."}


def _cover(payload: dict) -> dict:
    return {"reason": "Formulas never grant authority. Not a Guidewire rehost. Not legal advice."}


def _quant(payload: dict) -> dict:
    return {"fill": False, "reason": "A price is not a fill. Actuation SIMULATED. Not a LEAN rehost."}


def _title(payload: dict) -> dict:
    return {"deed": False, "reason": "Records receipt only. Not a deed. Not a Zillow rehost."}


def _retrieve(payload: dict) -> dict:
    q = str(payload.get("query") or payload.get("q") or "")
    return {
        "hits": [],
        "reason": "Empty evidence. Fail closed." if not q else "No index on this organ. Fail closed. Not a LlamaIndex/Haystack rehost.",
    }


def _observe(payload: dict) -> dict:
    return {"span": None, "reason": "YAWAR packet named. Trace backend not LIVE. Not a Phoenix rehost."}


def _tune(payload: dict) -> dict:
    return {"reason": "Unreceipted QLoRA refused. GPU ROADMAP. Not an Unsloth rehost."}


def _schema(payload: dict) -> dict:
    ok, reason = _schema_check(payload.get("schema"), payload.get("value"))
    return {
        "valid": ok,
        "reason": reason,
        "note": "Stdlib JSON types. Not constrained decode. Not Outlines/Instructor. Not LIVE.",
    }


def _energy(payload: dict) -> dict:
    return {
        "energy_j": None,
        "channel": "LIVE",
        "reason": "Joule UNAVAILABLE until RAPL/NVML MEASURED. Never a fabricated joule.",
    }


def _tool(payload: dict) -> dict:
    method = str(payload.get("method") or "")
    name = str(payload.get("name") or (payload.get("params") or {}).get("name") or "")
    if method in ("tools/list", "list"):
        return {
            "tools": [
                {
                    "name": "receipt.write",
                    "description": "Named YAWAR receipt tool. Ledger write is not LIVE.",
                }
            ],
            "ttlMs": 60000,
            "cacheScope": "organ",
            "note": "Allowlist. Unknown tools fail closed. Not an MCP rehost. Spec 2026-07-28 is cited, not copied.",
        }
    if name not in ALLOWED_TOOLS:
        return {
            "reason": f"unknown tool {name or '<empty>'!r}. Fail closed.",
            "allowlist": sorted(ALLOWED_TOOLS),
        }
    return {
        "reason": "receipt.write is named. Ledger bind is not LIVE. Fail closed.",
        "allowlist": sorted(ALLOWED_TOOLS),
    }


def _memory(payload: dict) -> dict:
    return {"facts": [], "reason": "Write refused without YAWAR. Not a Mem0/Zep rehost."}


def _eval(payload: dict) -> dict:
    return {"score": None, "reason": "No self-grading as LIVE. Not a RAGAS/HELM/Arena rehost."}


def _mesh(payload: dict) -> dict:
    return {"engine": None, "reason": "Overlay without an engine. Unknown engine fail closed. Not a Dynamo rehost."}


def _route(payload: dict) -> dict:
    provider = str(payload.get("provider") or payload.get("model") or "")
    key = str(payload.get("key") or payload.get("virtual_key") or "")
    if not key:
        return {"reason": "Virtual key required. Fail closed. Not a LiteLLM rehost."}
    if not provider:
        return {"reason": "Unknown provider. Fail closed."}
    return {"reason": f"Provider {provider!r} is not admitted. Fail closed. Budget UNAVAILABLE."}


def _cache(payload: dict) -> dict:
    return {"hit": False, "reason": "Miss. A cache hit is not a new thought. Not an LMCache rehost."}


def _voice(payload: dict) -> dict:
    return {"reason": "Audio is not authority. Duplex refused. Not a LiveKit/Cartesia/Deepgram rehost."}


def _sandbox(payload: dict) -> dict:
    code = str(payload.get("code") or payload.get("cmd") or "")
    return {
        "executed": False,
        "reason": "Exec refused. Escape is fail-closed." + (" Code was not run." if code else ""),
        "note": "Not a Daytona/E2B rehost.",
    }


def _identity(payload: dict) -> dict:
    agent = str(payload.get("agent") or payload.get("workload") or "")
    if not agent:
        return {"spiffe_shaped": None, "svid": None, "reason": "No agent. Fail closed. Not a SPIRE SVID."}
    digest = hashlib.sha256(f"szl-agent:{agent}".encode()).hexdigest()
    return {
        "spiffe_shaped": f"spiffe://szl.holdings/agent/{digest[:16]}",
        "svid": None,
        "reason": "UNSIGNED-honest id. Tamper-evident, not a certificate. Not SPIRE. Not Astrix.",
    }


def _rails(payload: dict) -> dict:
    topic = str(payload.get("topic") or payload.get("intent") or payload.get("text") or "").strip().lower()
    allowed = topic in RAIL_TOPICS
    return {
        "topic": topic or None,
        "allowed": False,
        "reason": (
            "Topic named but rails are not LIVE. Halt."
            if allowed
            else "Off-rail. Halt. Not NeMo. Not Colang."
        ),
    }


def _browser(payload: dict) -> dict:
    url = str(payload.get("url") or payload.get("action") or "")
    return {
        "navigated": False,
        "url": url or None,
        "reason": "No actuation. Browser refused. Not Playwright/Stagehand/Browserbase.",
    }


def _policy(payload: dict) -> dict:
    action = str(payload.get("action") or payload.get("tool") or "")
    if not action:
        return {"allow": False, "reason": "No action. Fail closed. Not Cedar. Not OPA."}
    if action not in ALLOWED_TOOLS:
        return {"allow": False, "reason": f"action {action!r} denied. Fail closed. Not Cedar/OPA."}
    return {"allow": False, "reason": "Named action, policy not LIVE. Fail closed."}


def _lyte(payload: dict) -> dict:
    return {
        "ok": True,
        "halt": False,
        "reason": "Bind only. Formulas never grant authority. Not a second flagship.",
    }


_HANDLERS = {
    "lyte": _lyte,
    "N1": _serve,
    "N2": _graph,
    "N3": _guard,
    "N4": _mosaic,
    "N5": _lattice,
    "N6": _cover,
    "N7": _quant,
    "N8": _title,
    "N9": _retrieve,
    "N10": _observe,
    "N11": _tune,
    "N12": _schema,
    "N13": _energy,
    "N14": _tool,
    "N15": _memory,
    "N16": _eval,
    "N17": _mesh,
    "N18": _route,
    "N19": _cache,
    "N20": _voice,
    "N21": _sandbox,
    "N22": _identity,
    "N23": _rails,
    "N24": _browser,
    "N25": _policy,
}


def roadmap() -> dict:
    organs = []
    for c in FRONTIERS:
        organs.append(
            {
                "cell": c.id,
                "title": c.title,
                "job": c.job,
                "phase": PHASE_STARTED,
                "honesty": c.honesty,
                "admitted": False,
                "live": False,
                "surface": "/api/act",
                "take": c.szl,
                "refuse": "Compile returns BLOCKED. Actuation fail-closed. Not LIVE.",
            }
        )
    return {
        "phase": PHASE_STARTED,
        "admitted": [LYTE.id],
        "started": [c.id for c in FRONTIERS],
        "live": [],
        "organs": organs,
        "lambda_status": "Conjecture 1",
        "energy": None,
        "signer": "UNSIGNED-honest",
        "note": "Every named theatre is STARTED as a fail-closed organ. STARTED is not LIVE. Compile still BLOCKED.",
    }


def act(cell_id: str, payload: dict | None = None) -> dict:
    """Run the fail-closed organ. Never returns live=True. Frontiers stay BLOCKED."""
    payload = payload if isinstance(payload, dict) else {}
    body = _base(cell_id, payload)
    cell = resolve_cell(cell_id)
    handler = _HANDLERS.get(cell.id if cell else "")
    extra = handler(payload) if handler else {"reason": "Unknown cell. Fail closed."}
    body.update(extra)
    if cell and cell.admitted:
        body["ok"] = True
        body["halt"] = False
        body["phase"] = PHASE_ADMITTED
    else:
        body["ok"] = False
        body["halt"] = True
        body["live"] = False
        if cell and cell.id == "N13":
            body["honesty"] = "UNAVAILABLE"
            body["energy"] = None
            body["energy_j"] = None
    body["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body["id"] = str(uuid.uuid4())
    sealed = {k: body[k] for k in body if k != "hash"}
    body["hash"] = _sha256(sealed)
    return body
