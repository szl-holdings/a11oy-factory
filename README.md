---
title: A11oy Factory
emoji: ⚖️
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
suggested_hardware: cpu-basic
short_description: Governed AI distribution compiler — locks, policy, SBOM, provenance, receipts.
---

# A11oy Factory

**A11oy Factory is the governed distribution layer for open-source AI
software.** It compiles exact upstream artifacts, target constraints, policy,
evidence, and dependency relationships into a deterministic distribution
bundle.

This is not another model host, container wrapper, or second flagship. It is
the trusted factory between frameworks/models and the CPU, CUDA, XPU, ROCm,
Arm, cloud, edge, and future A11oy/KHIPU hardware that runs them.

## Factory Core v1 — LIVE

The core now performs real, fail-closed work:

- validates catalog and target-profile contracts;
- resolves dependency closure deterministically and detects cycles;
- enforces immutable source pins, source-host allowlists, license policy,
  evidence requirements, target compatibility, size limits, and network policy;
- emits a content-addressed lock and non-executing build plan;
- emits an SPDX 2.3 SBOM;
- emits an in-toto Statement with SLSA v1 provenance;
- emits an A11oy hash-chained receipt and SHA-256 manifest;
- re-resolves and verifies the whole bundle;
- can explicitly materialize digest-pinned artifacts with streamed SHA-256,
  byte-count enforcement, atomic rename, and no execution.

The compiler is **LIVE**. A generated bundle states
`runtime_certified: false` until hardware execution, current vulnerability
evidence, compatibility testing, and a real cryptographic signer are attached.
Unknown input or missing proof fails closed.

```bash
python -m a11oy_factory distro validate \
  --catalog factory/catalog.json \
  --profile factory/profiles/vllm-cpu-amd64.json

python -m a11oy_factory distro bundle \
  --catalog factory/catalog.json \
  --profile factory/profiles/vllm-cpu-amd64.json \
  --out-dir dist/vllm-cpu-amd64

python -m a11oy_factory distro verify \
  --catalog factory/catalog.json \
  --profile factory/profiles/vllm-cpu-amd64.json \
  --lock dist/vllm-cpu-amd64/factory.lock.json \
  --sbom dist/vllm-cpu-amd64/factory.spdx.json \
  --provenance dist/vllm-cpu-amd64/factory.provenance.json
```

The initial checked-in catalog is a real upstream release snapshot:

| Component | Version | Targets | Integrity |
| --- | --- | --- | --- |
| PyTorch source | 2.13.0 | all initial Linux targets | release SHA-256 pinned |
| vLLM CPU wheel | 0.28.0 | AMD64, ARM64 | release SHA-256 pinned |
| vLLM CUDA wheel | 0.28.0 | CUDA 12.9 AMD64, ARM64 | release SHA-256 pinned |
| vLLM XPU wheel | 0.28.0 | Intel XPU AMD64 | release SHA-256 pinned |

Candidate profiles preserve vulnerability state as `UNVERIFIED`; integrity
proof is not misrepresented as a vulnerability scan or runtime certificate.
See [`factory/README.md`](./factory/README.md).

## Surfaces

| Surface | State |
| --- | --- |
| GitHub | `szl-holdings/a11oy-factory` · public |
| Hugging Face Space | `SZLHOLDINGS/a11oy-factory` · Docker |
| Factory Core v1 | LIVE · deterministic metadata distribution |
| Reference profiles | CPU AMD64/ARM64 · CUDA 12.9 AMD64/ARM64 · XPU AMD64 |
| Lyte window | `szl-holdings/lyte-services` · same compiler, not a flagship |
| Merge sink | `szl-holdings/evidence-studio` · one writer |
| Canonical flagship | `SZLHOLDINGS/a11oy` |
| a-11-oy.com production certificate | closed until independent evidence |
| Signing | `UNSIGNED-honest`; tamper-evident hash is not a signature |

## Decision Cell Compiler

The existing Decision Cell Compiler remains fail closed. **Lyte** is the one
admitted structural cell. N1–N27 are named theatres and do not become runtime
LIVE because the distribution compiler can describe them.

| Cell | Title | Cited job | Runtime state |
| --- | --- | --- | --- |
| lyte | Lyte | owner-admitted design-partner cell | STRUCTURAL-ONLY |
| N1 | Serve | vLLM / SGLang / Ollama / TensorRT-LLM | BLOCKED |
| N2 | Graph | LangGraph | BLOCKED |
| N3 | Guard | Llama Guard | BLOCKED |
| N4 | Mosaic | MosaicML / Databricks | BLOCKED |
| N5 | Lattice | SENTRA/YAWAR overlay | BLOCKED |
| N6 | Cover | Guidewire P&C core | BLOCKED |
| N7 | Quant | QuantConnect LEAN | BLOCKED |
| N8 | Title | public property records | BLOCKED |
| N9 | Retrieve | LlamaIndex / Haystack / Letta | BLOCKED |
| N10 | Observe | Phoenix / LangSmith / Langfuse / DeepEval | BLOCKED |
| N11 | Tune | Unsloth LoRA / QLoRA | BLOCKED |
| N12 | Schema | Outlines / Instructor | BLOCKED |
| N13 | Energy | RAPL / NVML joule channel | UNAVAILABLE |
| N14 | Tool | Model Context Protocol | BLOCKED |
| N15 | Memory | Mem0 / Zep Graphiti | BLOCKED |
| N16 | Eval | RAGAS / HELM / Arena | BLOCKED |
| N17 | Mesh | NVIDIA Dynamo / Ray Serve / llm-d | BLOCKED |
| N18 | Route | LiteLLM / OpenRouter / RouteLLM | BLOCKED |
| N19 | Cache | LMCache / Mooncake / GPTCache | BLOCKED |
| N20 | Voice | LiveKit / Cartesia / Deepgram | BLOCKED |
| N21 | Sandbox | Daytona / E2B | BLOCKED |
| N22 | Identity | SPIFFE / SPIRE / NHI policy | BLOCKED |
| N23 | Rails | NVIDIA NeMo Guardrails | BLOCKED |
| N24 | Browser | Playwright / Stagehand / Browserbase | BLOCKED |
| N25 | Policy | AWS Cedar / Open Policy Agent | BLOCKED |
| N26 | Inference | wrapped NVML/RAPL measurement | REPORTED, BLOCKED |
| N27 | Train | receipted GPU train gate | UNAVAILABLE |

```bash
python -m a11oy_factory compile --cell lyte
python -m a11oy_factory compile --cell N1
python -m a11oy_factory roadmap
python -m a11oy_factory act --cell N22 --payload '{"agent":"counsel"}'
python -m a11oy_factory search --q vllm
```

## Proof boundary

| Claim | State |
| --- | --- |
| Deterministic catalog/profile resolution | LIVE |
| Immutable release-asset pins | LIVE |
| License/evidence/target policy | LIVE |
| SPDX and SLSA documents | LIVE |
| Explicit artifact byte verification | LIVE when materialization is invoked |
| Vulnerability clearance | UNVERIFIED in candidate profiles |
| Runtime compatibility on target hardware | NOT_CERTIFIED |
| Production cryptographic signature | UNAVAILABLE |
| Energy measurement | UNAVAILABLE without readable RAPL/NVML |
| Λ uniqueness | Conjecture 1 OPEN |

Formulas never grant authority. Metadata integrity is not runtime safety.
`UNSIGNED-honest` is not Cosign, Fulcio, Rekor, or an ATO.
