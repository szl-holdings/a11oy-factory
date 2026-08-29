"""Admitted and ROADMAP decision cells. Fail closed on anything else.

N1–N26 are named category-capture theatres. We cite the leader of the job
and take the job, not the code. Compiler refuses admission until doctrine
names a cell LIVE. Lyte is the only admitted cell.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Honesty = Literal[
    "STRUCTURAL-ONLY",
    "ROADMAP",
    "CONJECTURE",
    "REPORTED",
    "UNAVAILABLE",
]


@dataclass(frozen=True)
class Cell:
    id: str
    title: str
    organ: str
    honesty: Honesty
    admitted: bool
    bind: str
    note: str
    job: str = ""
    cite: str = ""
    szl: str = ""


LYTE = Cell(
    id="lyte",
    title="Lyte",
    organ="heart",
    honesty="STRUCTURAL-ONLY",
    admitted=True,
    bind="BIND_AS_A11OY_PACKAGE",
    job="design-partner cell",
    cite="Owner-admitted. Not a flagship.",
    szl="Schema-checked bind into a11oy. Formulas never grant authority.",
    note="The one admitted cell. Schema-checked bind into a11oy. Not a flagship.",
)


def _frontier(
    n: int,
    *,
    title: str,
    organ: str,
    job: str,
    cite: str,
    szl: str,
) -> Cell:
    return Cell(
        id=f"N{n}",
        title=title,
        organ=organ,
        honesty="ROADMAP",
        admitted=False,
        bind="BIND_AS_A11OY_PACKAGE",
        job=job,
        cite=cite,
        szl=szl,
        note=(
            f"{title}. Cite {cite}. SZL takes the job: {szl} "
            "Compiler refuses admission until doctrine names it LIVE."
        ),
    )


FRONTIERS: tuple[Cell, ...] = (
    _frontier(
        1,
        title="Serve",
        organ="brain",
        job="inference serving",
        cite=(
            "vLLM (production default, PagedAttention, continuous batching, OpenAI /v1); "
            "SGLang (RadixAttention prefix reuse, agentic/structured); "
            "Ollama (local DX wrapping llama.cpp); "
            "TensorRT-LLM (NVIDIA hardware-optimized)"
        ),
        szl="receipted fail-closed serving with schema outside the weights. Not a vLLM/SGLang/Ollama/TensorRT rehost.",
    ),
    _frontier(
        2,
        title="Graph",
        organ="nervous",
        job="agent orchestration",
        cite=(
            "LangGraph (stateful cyclic multi-agent, durable execution, "
            "checkpointing, human-in-the-loop interrupt())"
        ),
        szl="doctrine-bound graph with SENTRA on every edge. Not a LangGraph rehost.",
    ),
    _frontier(
        3,
        title="Guard",
        organ="immune",
        job="input/output safeguard",
        cite=(
            "Llama Guard (prompt and response classification, risk taxonomy; "
            "Llama-Guard-4 multimodal)"
        ),
        szl="SENTRA tripwires plus WILLAY conscience. Not a Llama Guard rehost.",
    ),
    _frontier(
        4,
        title="Mosaic",
        organ="circulatory",
        job="data mosaic",
        cite="MosaicML / Databricks Mosaic AI (train, customize, and deploy on own data, lakehouse)",
        szl="receipted mosaic with UNSIGNED-honest lineage. Not a Databricks rehost.",
    ),
    _frontier(
        5,
        title="Lattice",
        organ="immune",
        job="defense overlay",
        cite="immune-lattice COP (SENTRA/YAWAR). Hub vertical may be LIVE; this frontier bind is not.",
        szl="defense overlay on every cell. Hunt, isolate, deceive. Never strike people. Bind stays ROADMAP.",
    ),
    _frontier(
        6,
        title="Cover",
        organ="heart",
        job="P&C insurance core",
        cite="Guidewire (policy, billing, claims; 570+ insurers)",
        szl="allodial/counsel bind. Formulas never grant authority. Not a Guidewire rehost.",
    ),
    _frontier(
        7,
        title="Quant",
        organ="brain",
        job="algorithmic research and backtest",
        cite="QuantConnect LEAN (research, backtest, live trade on many venues)",
        szl="receipted backtest. Actuation SIMULATED. Not a broker. Not a LEAN rehost.",
    ),
    _frontier(
        8,
        title="Title",
        organ="skeleton",
        job="property records",
        cite="Zillow (residential listings and records). szl-real-estate is a LIVE Hub vertical; this frontier bind is not.",
        szl="receipted title/underwrite bind. Not a Zillow rehost. Bind stays ROADMAP.",
    ),
    _frontier(
        9,
        title="Retrieve",
        organ="nervous",
        job="retrieval and memory",
        cite=(
            "LlamaIndex (data ingestion, indexing, RAG); "
            "Haystack (production pipelines); "
            "Letta / MemGPT (persistent agent memory)"
        ),
        szl="receipted retrieval with SENTRA on every chunk. Not a LlamaIndex/Haystack/Letta rehost.",
    ),
    _frontier(
        10,
        title="Observe",
        organ="immune",
        job="trace and evaluation",
        cite=(
            "Arize Phoenix (OpenTelemetry-native traces and evals); "
            "LangSmith (LangChain traces); "
            "Langfuse (OSS traces); "
            "DeepEval (CI evals)"
        ),
        szl="YAWAR receipt traces. UNSIGNED-honest. Not a Phoenix/LangSmith rehost.",
    ),
    _frontier(
        11,
        title="Tune",
        organ="brain",
        job="receipted fine-tune",
        cite="Unsloth (LoRA / QLoRA, 2× faster, 70% less VRAM). Fine-tunes only against LIVE weights.",
        szl="receipted QLoRA on own data. GPU ROADMAP. Not an Unsloth rehost.",
    ),
    _frontier(
        12,
        title="Schema",
        organ="skeleton",
        job="constrained generation",
        cite=(
            "Outlines (finite-state constrained decode); "
            "Instructor (Pydantic structured outputs); "
            "SGLang structured (JSON-mode / tool-call)"
        ),
        szl="schema stays outside the weights. Constrained decode as a job. Not an Outlines/Instructor rehost.",
    ),
    Cell(
        id="N13",
        title="Energy",
        organ="nervous",
        honesty="UNAVAILABLE",
        admitted=False,
        bind="BIND_AS_A11OY_PACKAGE",
        job="measured energy channel",
        cite="Intel RAPL package counter; NVIDIA NVML nvmlDeviceGetTotalEnergyConsumption",
        szl="LIVE probe. Joule MEASURED only from RAPL or NVML. Never a fabricated joule. Not an Electricity Maps clone.",
        note=(
            "Energy channel is LIVE. Joule stays UNAVAILABLE until RAPL or NVML "
            "is readable on the box. Compiler refuses admission of a fabricated joule."
        ),
    ),
    _frontier(
        14,
        title="Tool",
        organ="nervous",
        job="agent tool protocol",
        cite=(
            "Anthropic Model Context Protocol (open standard for connecting agents to tools and data; "
            "2026-07-28 spec is production-grade, stateless, HTTP-revalidatable)"
        ),
        szl="SENTRA-gated tools. Fail closed on unknown tools. Not an MCP rehost.",
    ),
    _frontier(
        15,
        title="Memory",
        organ="brain",
        job="persistent agent memory",
        cite=(
            "Mem0 (extract-and-retrieve, hybrid vector/graph/kv); "
            "Zep Graphiti (temporal knowledge graph, LongMemEval leader)"
        ),
        szl="receipted memory with YAWAR lineage. Not a Mem0/Zep rehost. Letta stays cited on N9.",
    ),
    _frontier(
        16,
        title="Eval",
        organ="immune",
        job="offline evaluation",
        cite=(
            "RAGAS (RAG faithfulness/precision/recall); "
            "Stanford HELM (holistic eval); "
            "LMSYS Chatbot Arena (pairwise live votes)"
        ),
        szl="receipted eval. No self-grading as LIVE. Not a RAGAS/HELM/Arena rehost.",
    ),
    _frontier(
        17,
        title="Mesh",
        organ="circulatory",
        job="distributed inference",
        cite=(
            "NVIDIA Dynamo (disaggregated prefill/decode, orchestration above vLLM/SGLang/TRT-LLM); "
            "Ray Serve LLM; "
            "llm-d (Kubernetes-native distributed inference)"
        ),
        szl="receipted distributed overlay. Not a Dynamo/Ray/llm-d rehost.",
    ),
    _frontier(
        18,
        title="Route",
        organ="circulatory",
        job="LLM gateway and routing",
        cite=(
            "LiteLLM (open-source OpenAI-format proxy, fallback, spend, 100+ providers); "
            "OpenRouter (hosted marketplace aggregator); "
            "RouteLLM (LMSYS/Berkeley learned routing, not a gateway)"
        ),
        szl="Receipted gateway. Fail closed on unknown providers. Not a LiteLLM/OpenRouter rehost.",
    ),
    _frontier(
        19,
        title="Cache",
        organ="circulatory",
        job="prefix and semantic cache",
        cite=(
            "LMCache (KV offload for vLLM/SGLang); "
            "Mooncake (KV transfer plane); "
            "GPTCache (semantic response cache)"
        ),
        szl="Receipted reuse. A cache hit is not a new thought. Not an LMCache/Mooncake/GPTCache rehost.",
    ),
    _frontier(
        20,
        title="Voice",
        organ="nervous",
        job="realtime duplex voice",
        cite=(
            "LiveKit Agents (realtime rooms and agent worker); "
            "Cartesia (low-latency TTS); "
            "Deepgram (streaming STT)"
        ),
        szl="Receipted duplex. Audio is not authority. Not a LiveKit/Cartesia/Deepgram rehost.",
    ),
    _frontier(
        21,
        title="Sandbox",
        organ="skeleton",
        job="isolated agent code execution",
        cite=(
            "Daytona (agent-native sandboxed workspaces); "
            "E2B (firecracker microVM code interpreter)"
        ),
        szl="SENTRA-gated exec. Fail closed on escape. Not a Daytona/E2B rehost.",
    ),
    _frontier(
        22,
        title="Identity",
        organ="skeleton",
        job="non-human agent identity",
        cite=(
            "SPIFFE/SPIRE (workload SVID, not a person); "
            "Astrix (NHI fingerprinting and agent policy, RSAC 2026)"
        ),
        szl="UNSIGNED-honest spiffe-shaped id. Not an SVID. Not a certificate. Not an Astrix rehost.",
    ),
    _frontier(
        23,
        title="Rails",
        organ="immune",
        job="conversation rails",
        cite=(
            "NVIDIA NeMo Guardrails (Colang dialog/input/output/retrieval/execution rails — "
            "conversation flow, not a safety classifier; distinct from Llama Guard on N3)"
        ),
        szl="Topic rails as a state machine. Off-rail HALT. Not Colang. Not a NeMo rehost.",
    ),
    _frontier(
        24,
        title="Browser",
        organ="nervous",
        job="agent browser actuation",
        cite=(
            "Playwright (control loop); "
            "Stagehand (Browserbase act/extract/observe); "
            "Browserbase (managed Chromium)"
        ),
        szl="No actuation. Navigation refused. Not a Playwright/Stagehand/Browserbase rehost.",
    ),
    _frontier(
        25,
        title="Policy",
        organ="immune",
        job="authorization policy for tools",
        cite=(
            "AWS Cedar (policy-as-code authorization); "
            "Open Policy Agent (Rego)"
        ),
        szl="SENTRA policy. Unknown action fail closed. Not a Cedar/OPA rehost.",
    ),
    Cell(
        id="N26",
        title="Inference",
        organ="nervous",
        honesty="REPORTED",
        admitted=False,
        bind="BIND_AS_A11OY_PACKAGE",
        job="wrapped inference joule",
        cite="szl-command-lab GET /api/energy/inference NVML wrap on T4; Intel RAPL package wrap",
        szl=(
            "Joule is REPORTED from the command-lab wrap, never MEASURED on this CPU factory. "
            "Not a second meter. Not an elevation. Compiler stays BLOCKED."
        ),
        note=(
            "Inference joule is the NVML/RAPL delta around a wrapped kernel on command-lab. "
            "This factory box has no meter. Honesty is REPORTED, not MEASURED. "
            "Never a fabricated joule. Compiler refuses admission."
        ),
    ),
)

CELLS: dict[str, Cell] = {LYTE.id: LYTE, **{c.id: c for c in FRONTIERS}}
ADMITTED = frozenset(c.id for c in CELLS.values() if c.admitted)

_ALIASES: dict[str, str] = {
    "serve": "N1",
    "serving": "N1",
    "inference": "N1",
    "graph": "N2",
    "orchestration": "N2",
    "guard": "N3",
    "safeguard": "N3",
    "mosaic": "N4",
    "lattice": "N5",
    "cover": "N6",
    "insurance": "N6",
    "quant": "N7",
    "lean": "N7",
    "title": "N8",
    "zillow": "N8",
    "retrieve": "N9",
    "retrieval": "N9",
    "retrive": "N9",
    "retriev": "N9",
    "rag": "N9",
    "observe": "N10",
    "observability": "N10",
    "obsv": "N10",
    "observ": "N10",
    "eval": "N16",
    "ragas": "N16",
    "helm": "N16",
    "arena": "N16",
    "tune": "N11",
    "qlora": "N11",
    "unsloth": "N11",
    "schema": "N12",
    "outlines": "N12",
    "instructor": "N12",
    "energy": "N13",
    "joule": "N13",
    "rapl": "N13",
    "nvml": "N13",
    "tool": "N14",
    "mcp": "N14",
    "memory": "N15",
    "mem0": "N15",
    "zep": "N15",
    "mesh": "N17",
    "dynamo": "N17",
    "route": "N18",
    "litellm": "N18",
    "openrouter": "N18",
    "gateway": "N18",
    "cache": "N19",
    "lmcache": "N19",
    "mooncake": "N19",
    "gptcache": "N19",
    "voice": "N20",
    "livekit": "N20",
    "cartesia": "N20",
    "deepgram": "N20",
    "sandbox": "N21",
    "daytona": "N21",
    "e2b": "N21",
    "identity": "N22",
    "spiffe": "N22",
    "spire": "N22",
    "astrix": "N22",
    "nhi": "N22",
    "rails": "N23",
    "nemo": "N23",
    "colang": "N23",
    "browser": "N24",
    "playwright": "N24",
    "stagehand": "N24",
    "browserbase": "N24",
    "policy": "N25",
    "cedar": "N25",
    "opa": "N25",
    "inference wrap": "N26",
    "wrapped joule": "N26",
    "n26": "N26",
}


def resolve_cell(cell_id: str) -> Cell | None:
    """Resolve id, case, or title/alias. Unknown returns None (fail closed)."""
    key = (cell_id or "").strip()
    if not key:
        return None
    cell = CELLS.get(key) or CELLS.get(key.lower()) or CELLS.get(key.upper())
    if cell:
        return cell
    low = key.lower().replace("_", " ").replace("-", " ").strip()
    alias = _ALIASES.get(low)
    if alias:
        return CELLS.get(alias)
    for c in CELLS.values():
        if c.title.lower() == low or c.job.lower() == low:
            return c
    return None
