"""Admitted and ROADMAP decision cells. Fail closed on anything else.

N1–N12 are named category-capture theatres. We cite the leader of the job
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
    "eval": "N10",
    "tune": "N11",
    "qlora": "N11",
    "unsloth": "N11",
    "schema": "N12",
    "outlines": "N12",
    "instructor": "N12",
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
