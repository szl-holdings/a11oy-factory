# A11oy Trusted AI Factory

This directory is the first production-shaped slice of the **AI distribution
factory**: the layer between upstream models/frameworks and the machines that
run them.

It is intentionally not another model host, container wrapper, or package
mirror. The factory compiles trusted metadata into deterministic artifacts:

1. a target-specific dependency lock;
2. a non-executing build/materialization plan;
3. an SPDX 2.3 software bill of materials;
4. an in-toto Statement carrying SLSA v1 provenance;
5. a hash-chained A11oy receipt;
6. a verification report and SHA-256 manifest.

The compiler is **LIVE**. Runtime behavior is **NOT_CERTIFIED** until hardware,
vulnerability, compatibility, and execution evidence are attached. Unknown
inputs and policy violations fail closed.

## Checked-in reference catalog

The initial catalog is a real upstream release snapshot, not placeholder data:

- PyTorch `2.13.0` source distribution, pinned by its published SHA-256.
- vLLM `0.28.0` release wheels for:
  - Linux AMD64 CPU;
  - Linux ARM64 CPU;
  - Linux AMD64 CUDA 12.9;
  - Linux ARM64 CUDA 12.9;
  - Linux AMD64 Intel XPU.

Each vLLM variant depends on the exact PyTorch version declared by the vLLM
`v0.28.0` build metadata. Every source has an immutable digest, exact byte
length, declared license, target constraints, evidence links, and an explicit
vulnerability-evidence state.

`UNVERIFIED` vulnerability state is permitted only in the candidate profiles
and is preserved as a warning in every lock and receipt. A release policy can
change `permitted_vulnerability_status` to `["VERIFIED"]`; the same catalog will
then block until scanner evidence is present.

## Commands

```bash
# Validate the catalog and one target profile.
python -m a11oy_factory distro validate \
  --catalog factory/catalog.json \
  --profile factory/profiles/vllm-cpu-amd64.json

# Generate the complete deterministic bundle.
python -m a11oy_factory distro bundle \
  --catalog factory/catalog.json \
  --profile factory/profiles/vllm-cpu-amd64.json \
  --out-dir dist/vllm-cpu-amd64

# Re-resolve and verify every generated document.
python -m a11oy_factory distro verify \
  --catalog factory/catalog.json \
  --profile factory/profiles/vllm-cpu-amd64.json \
  --lock dist/vllm-cpu-amd64/factory.lock.json \
  --sbom dist/vllm-cpu-amd64/factory.spdx.json \
  --provenance dist/vllm-cpu-amd64/factory.provenance.json
```

Artifact download is a separate, explicit operation. It accepts only HTTPS
sources on the policy allowlist, streams to a temporary file, enforces the
locked byte count, verifies SHA-256, atomically renames the file, and never
executes it:

```bash
python -m a11oy_factory distro materialize \
  --lock dist/vllm-cpu-amd64/factory.lock.json \
  --component vllm-cpu-amd64 \
  --out-dir dist/artifacts
```

## Trust boundary

| Proof | Current state |
| --- | --- |
| Catalog and profile schema | Verified locally |
| Dependency closure and cycle detection | Verified locally |
| Target compatibility declarations | Enforced |
| Source immutability | Enforced by commit or SHA-256 |
| License policy | Enforced |
| Source-host allowlist | Enforced |
| SPDX 2.3 SBOM | Generated deterministically |
| in-toto/SLSA provenance | Generated deterministically |
| Receipt and bundle hashes | Verified |
| Upstream artifact bytes | Verified only after explicit materialization |
| Current vulnerability state | `UNVERIFIED` in candidate profiles |
| Runtime behavior on target hardware | `NOT_CERTIFIED` |
| Cryptographic signing | `UNSIGNED-honest` until a real signer is wired |

## Expansion contract

New frameworks, runtimes, accelerators, models, and vertical packages enter
through the same catalog contract. They do not become release-grade because a
README says so. Promotion requires immutable source identity, license evidence,
compatibility evidence, vulnerability evidence, reproducible bundle output,
hardware execution receipts, and policy approval.

This is the factory's moat: **one governed dependency graph and one proof
format across CPU, CUDA, XPU, ROCm, Arm, cloud, edge, and future A11oy/KHIPU
hardware profiles.**
