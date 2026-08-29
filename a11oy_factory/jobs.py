"""Web-cited jobs versus SZL organs. Search our catalog, not a live scrape.

We searched the leaders, encoded the job, and refuse to rehost the code.
Signing stays UNSIGNED-honest (tamper-evident, not Sigstore/Cosign).
Energy stays UNAVAILABLE. Λ stays Conjecture 1.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .cells import FRONTIERS, LYTE, Cell

# Typo / shorthand → canonical needle. Search is catalog, not a live crawl.
ALIASES: dict[str, str] = {
    "vlm": "vllm",
    "v-llm": "vllm",
    "vlmm": "vllm",
    "sgl": "sglang",
    "langraph": "langgraph",
    "lang graph": "langgraph",
    "llama-guard": "llama guard",
    "llamaguard": "llama guard",
    "retrive": "retrieve",
    "retriev": "retrieve",
    "rag": "llamaindex",
    "llama-index": "llamaindex",
    "llama index": "llamaindex",
    "memgpt": "letta",
    "obsv": "observe",
    "observ": "observe",
    "observability": "phoenix",
    "otel": "phoenix",
    "opentelemetry": "phoenix",
    "qlora": "unsloth",
    "lora": "unsloth",
    "finetune": "unsloth",
    "fine-tune": "unsloth",
    "json-mode": "outlines",
    "jsonmode": "outlines",
    "structured": "outlines",
    "pydantic": "instructor",
    "trt": "tensorrt",
    "tensorrt-llm": "tensorrt",
    "n9": "retrieve",
    "n10": "observe",
    "n11": "tune",
    "n12": "schema",
}


@dataclass(frozen=True)
class Job:
    id: str
    title: str
    leader: str
    url: str
    organ: str
    cell: str
    honesty: str
    admitted: bool
    take: str
    refuse: str


JOBS: tuple[Job, ...] = (
    Job(
        id="lyte",
        title="Lyte design-partner cell",
        leader="SZL owner order",
        url="https://github.com/szl-holdings/a11oy-factory",
        organ="heart",
        cell="lyte",
        honesty="STRUCTURAL-ONLY",
        admitted=True,
        take="BIND_AS_A11OY_PACKAGE. Schema-checked bind into a11oy.",
        refuse="Not a second flagship. Formulas never grant authority.",
    ),
    Job(
        id="vllm",
        title="Production LLM serving",
        leader="vLLM",
        url="https://github.com/vllm-project/vllm",
        organ="brain",
        cell="N1",
        honesty="ROADMAP",
        admitted=False,
        take="Receipted fail-closed serving. Schema outside the weights. OpenAI-shaped /v1.",
        refuse="Do not rehost vLLM, PagedAttention, or their kernels.",
    ),
    Job(
        id="sglang",
        title="Agentic / structured serving",
        leader="SGLang",
        url="https://github.com/sgl-project/sglang",
        organ="brain",
        cell="N1",
        honesty="ROADMAP",
        admitted=False,
        take="Prefix-reuse and structured output as a serving job, under receipts.",
        refuse="Do not rehost RadixAttention or SGLang runtime.",
    ),
    Job(
        id="ollama",
        title="Local developer serving",
        leader="Ollama",
        url="https://github.com/ollama/ollama",
        organ="brain",
        cell="N1",
        honesty="ROADMAP",
        admitted=False,
        take="Honest local DX path wrapping llama.cpp. CPU-honest until GPU is MEASURED.",
        refuse="Do not rehost Ollama. Do not claim GPU serve LIVE.",
    ),
    Job(
        id="tensorrt",
        title="Hardware-optimized serving",
        leader="TensorRT-LLM",
        url="https://github.com/NVIDIA/TensorRT-LLM",
        organ="brain",
        cell="N1",
        honesty="ROADMAP",
        admitted=False,
        take="Receipted serve on measured NVIDIA hardware. Energy stays UNAVAILABLE until NVML.",
        refuse="Do not rehost TensorRT-LLM. Do not fabricate GPU LIVE.",
    ),
    Job(
        id="langgraph",
        title="Stateful agent graph",
        leader="LangGraph",
        url="https://www.langchain.com/langgraph",
        organ="nervous",
        cell="N2",
        honesty="ROADMAP",
        admitted=False,
        take="Durable graph, checkpoint, human-in-the-loop. SENTRA on every edge.",
        refuse="Do not rehost LangGraph StateGraph or interrupt().",
    ),
    Job(
        id="llamaguard",
        title="Prompt and response safeguard",
        leader="Llama Guard",
        url="https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/",
        organ="immune",
        cell="N3",
        honesty="ROADMAP",
        admitted=False,
        take="Classify prompt and response. Fail closed on taxonomy hits.",
        refuse="Do not rehost Llama Guard weights or Purple Llama.",
    ),
    Job(
        id="mosaic",
        title="Own-data mosaic",
        leader="MosaicML / Databricks Mosaic AI",
        url="https://www.databricks.com/blog/databricks-mosaicml",
        organ="circulatory",
        cell="N4",
        honesty="ROADMAP",
        admitted=False,
        take="Receipted mosaic with UNSIGNED-honest lineage on own data.",
        refuse="Do not rehost MosaicML, Mosaic AI, or the lakehouse.",
    ),
    Job(
        id="lattice",
        title="Defense overlay",
        leader="immune-lattice",
        url="https://github.com/szl-holdings/immune-lattice",
        organ="immune",
        cell="N5",
        honesty="ROADMAP",
        admitted=False,
        take="SENTRA/YAWAR overlay on every cell. Defense only.",
        refuse="Hub vertical may be LIVE. This frontier bind is not. Never strike people.",
    ),
    Job(
        id="guidewire",
        title="P&C insurance core",
        leader="Guidewire",
        url="https://www.guidewire.com/",
        organ="heart",
        cell="N6",
        honesty="ROADMAP",
        admitted=False,
        take="Allodial/counsel bind for policy, billing, claims jobs.",
        refuse="Do not rehost Guidewire InsuranceSuite. Formulas never grant authority.",
    ),
    Job(
        id="quantconnect",
        title="Algorithmic research and backtest",
        leader="QuantConnect LEAN",
        url="https://www.quantconnect.com/",
        organ="brain",
        cell="N7",
        honesty="ROADMAP",
        admitted=False,
        take="Receipted backtest. Actuation SIMULATED.",
        refuse="Not a broker. Do not rehost LEAN. A price is not a fill.",
    ),
    Job(
        id="zillow",
        title="Property records",
        leader="Zillow",
        url="https://www.zillow.com/",
        organ="skeleton",
        cell="N8",
        honesty="ROADMAP",
        admitted=False,
        take="Receipted title/underwrite bind on public records.",
        refuse="Do not rehost Zillow. szl-real-estate Hub vertical may be LIVE; this bind is not.",
    ),
    Job(
        id="llamaindex",
        title="Retrieval-augmented generation",
        leader="LlamaIndex",
        url="https://github.com/run-llama/llama_index",
        organ="nervous",
        cell="N9",
        honesty="ROADMAP",
        admitted=False,
        take="Receipted retrieve. SENTRA on every chunk. Schema outside the weights.",
        refuse="Do not rehost LlamaIndex, its indices, or its query engines.",
    ),
    Job(
        id="haystack",
        title="Production retrieval pipelines",
        leader="Haystack",
        url="https://github.com/deepset-ai/haystack",
        organ="nervous",
        cell="N9",
        honesty="ROADMAP",
        admitted=False,
        take="Pipeline job under receipts. Fail closed on empty evidence.",
        refuse="Do not rehost Haystack pipelines.",
    ),
    Job(
        id="letta",
        title="Persistent agent memory",
        leader="Letta / MemGPT",
        url="https://github.com/letta-ai/letta",
        organ="nervous",
        cell="N9",
        honesty="ROADMAP",
        admitted=False,
        take="Memory as a receipted organ. Not a second brain without SENTRA.",
        refuse="Do not rehost Letta or MemGPT.",
    ),
    Job(
        id="phoenix",
        title="OpenTelemetry LLM traces and evals",
        leader="Arize Phoenix",
        url="https://github.com/Arize-ai/phoenix",
        organ="immune",
        cell="N10",
        honesty="ROADMAP",
        admitted=False,
        take="YAWAR receipt traces. Honest UNAVAILABLE over fabricated green.",
        refuse="Do not rehost Phoenix. Phoenix is ELv2, not Apache-2.0.",
    ),
    Job(
        id="langsmith",
        title="LangChain agent traces",
        leader="LangSmith",
        url="https://www.langchain.com/langsmith",
        organ="immune",
        cell="N10",
        honesty="ROADMAP",
        admitted=False,
        take="Trace every SENTRA edge. Receipt the cycle.",
        refuse="Do not rehost LangSmith.",
    ),
    Job(
        id="langfuse",
        title="OSS LLM traces",
        leader="Langfuse",
        url="https://github.com/langfuse/langfuse",
        organ="immune",
        cell="N10",
        honesty="ROADMAP",
        admitted=False,
        take="Self-hostable traces as YAWAR packets.",
        refuse="Do not rehost Langfuse.",
    ),
    Job(
        id="deepeval",
        title="CI evaluation",
        leader="DeepEval",
        url="https://github.com/confident-ai/deepeval",
        organ="immune",
        cell="N10",
        honesty="ROADMAP",
        admitted=False,
        take="Eval in CI with UNSIGNED-honest receipts. Never grade our own homework LIVE.",
        refuse="Do not rehost DeepEval or claim eval LIVE.",
    ),
    Job(
        id="unsloth",
        title="Receipted QLoRA",
        leader="Unsloth",
        url="https://github.com/unslothai/unsloth",
        organ="brain",
        cell="N11",
        honesty="ROADMAP",
        admitted=False,
        take="Fine-tunes only against LIVE weights with a receipt. GPU ROADMAP.",
        refuse="No unreceipted QLoRA. Not an Unsloth rehost.",
    ),
    Job(
        id="outlines",
        title="Constrained decode",
        leader="Outlines",
        url="https://github.com/dottxt-ai/outlines",
        organ="skeleton",
        cell="N12",
        honesty="ROADMAP",
        admitted=False,
        take="Finite-state schema outside the weights.",
        refuse="Do not rehost Outlines or its FSMs.",
    ),
    Job(
        id="instructor",
        title="Pydantic structured outputs",
        leader="Instructor",
        url="https://github.com/instructor-ai/instructor",
        organ="skeleton",
        cell="N12",
        honesty="ROADMAP",
        admitted=False,
        take="Typed receipts. Schema stays outside the weights.",
        refuse="Do not rehost Instructor.",
    ),
    Job(
        id="sigstore",
        title="Keyless artifact signing",
        leader="Sigstore / Cosign",
        url="https://www.sigstore.dev/",
        organ="skeleton",
        cell="",
        honesty="STRUCTURAL-ONLY",
        admitted=False,
        take="UNSIGNED-honest SHA-256 is tamper-EVIDENT.",
        refuse="Not a signature. Not Cosign. Not Fulcio. Signing stays STRUCTURAL-ONLY.",
    ),
    Job(
        id="energy",
        title="Grid carbon / joule accounting",
        leader="Electricity Maps",
        url="https://www.electricitymaps.com/",
        organ="circulatory",
        cell="",
        honesty="UNAVAILABLE",
        admitted=False,
        take="Energy remains UNAVAILABLE until NVML is MEASURED.",
        refuse="Do not fabricate joules. Do not clone Electricity Maps.",
    ),
)


def _blob(job: Job) -> str:
    return " ".join(
        [
            job.id,
            job.title,
            job.leader,
            job.organ,
            job.cell,
            job.honesty,
            job.take,
            job.refuse,
        ]
    ).lower()


def _cell_blob(cell: Cell) -> str:
    return " ".join(
        [cell.id, cell.title, cell.job, cell.cite, cell.szl, cell.note, cell.organ]
    ).lower()


def _needles(q: str) -> list[str]:
    raw = (q or "").strip().lower()
    if not raw:
        return []
    expanded = ALIASES.get(raw, raw)
    out: list[str] = []
    for n in (raw, expanded):
        if n and n not in out:
            out.append(n)
    # Only tokenize an alias expansion (vlm → vllm stays one token).
    # Never split "llama guard" into "llama"+"guard" — that hits Ollama.
    if " " not in raw and " " in expanded:
        for t in expanded.split():
            if t and t not in out:
                out.append(t)
    return out


def search_jobs(q: str) -> dict:
    """Local catalog search. Empty query returns the full table. Unknown query is empty hits, not an error."""
    needles = _needles(q)
    jobs = [asdict(j) for j in JOBS if not needles or any(n in _blob(j) for n in needles)]
    cells = [
        c.__dict__
        for c in (LYTE, *FRONTIERS)
        if not needles or any(n in _cell_blob(c) for n in needles)
    ]
    return {
        "query": q or "",
        "jobs": jobs,
        "cells": cells,
        "lambda_status": "Conjecture 1",
        "energy": None,
        "signer": "UNSIGNED-honest",
        "note": "Catalog of cited jobs. Not a live web crawl. We take the job, not the code.",
    }
