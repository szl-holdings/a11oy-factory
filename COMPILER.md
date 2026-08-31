# A11oy Factory Compilers

`BIND_AS_A11OY_PACKAGE`. Not a second flagship.

A11oy Factory contains two deliberately separate compilers.

## 1. Trusted AI Distribution Compiler — LIVE

The distribution compiler is production-shaped metadata infrastructure. It:

- validates catalog and target profile contracts;
- resolves dependency closure deterministically;
- detects missing dependencies and cycles;
- enforces immutable source identity, license rules, source-host allowlists,
  evidence requirements, artifact size caps, target compatibility, and network
  policy;
- generates a content-addressed lock, plan-only build graph, SPDX 2.3 SBOM,
  in-toto/SLSA provenance, A11oy receipt, verification report, and SHA256SUMS;
- optionally materializes selected release artifacts, streaming and verifying
  exact size and SHA-256 before atomic rename;
- never executes a downloaded artifact.

```bash
python -m unittest discover -s tests -v

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

`LIVE` here means the deterministic compiler and verifier run. It does not
mean an upstream model or framework has been certified on target hardware.

## 2. Decision Cell Compiler — fail closed

Lyte is the one admitted structural cell. N1–N27 are named theatres. The
Decision Cell Compiler refuses their runtime admission until doctrine and
evidence name them LIVE.

| Surface | Honesty |
|---|---|
| Trusted AI Distribution Compiler | LIVE |
| Distribution runtime certification | NOT_CERTIFIED |
| Distribution vulnerability state | UNVERIFIED in candidate profiles |
| Distribution signing | UNSIGNED-honest |
| Decision Cell Compiler | LIVE, fail closed |
| Admitted Lyte cell | STRUCTURAL-ONLY |
| N1–N12, N14–N25 | BLOCKED |
| N13 Energy | UNAVAILABLE without readable RAPL/NVML |
| N26 Inference energy | REPORTED, BLOCKED |
| N27 Train | UNAVAILABLE |
| Λ uniqueness | Conjecture 1 OPEN |

```bash
python -m a11oy_factory compile --cell lyte
python -m a11oy_factory compile --cell N1
python -m a11oy_factory roadmap
python -m a11oy_factory act --cell N14 --payload '{"method":"tools/list"}'
python -m a11oy_factory search --q vllm
```

Public APIs:

- `GET /api/distribution`
- `GET /api/distribution/catalog`
- `GET /api/distribution/profiles`
- `GET /api/distribution/profiles/{id}`
- `POST /api/distribution/resolve`
- `POST /api/distribution/verify`
- `GET /api/cells`
- `GET /api/jobs`
- `GET /api/search?q=`
- `GET /api/roadmap`
- `POST /api/compile`
- `POST /api/act`

Hash evidence is tamper-evident, not a cryptographic signature. Metadata
integrity is not vulnerability clearance, runtime compatibility, an ATO, or
human authority.

Canonical flagship remains `szl-holdings/a11oy`.
