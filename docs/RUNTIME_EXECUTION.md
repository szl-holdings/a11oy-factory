# Runtime execution qualification

A11oy Factory separates four assurance layers:

1. **Resolution** — catalog and profile inputs deterministically produce an immutable dependency lock.
2. **Artifact qualification** — upstream bytes are downloaded, redirect-policy checked, size checked, SHA-256 checked, independently rehashed, and receipted.
3. **Scoped runtime execution** — exact qualified wheels are installed and a pinned model revision must generate tokens through the native runtime on a named target.
4. **Production certification** — broader hardware, workload, security, performance, availability, and operational evidence. This layer is not implied by a smoke proof.

The `vllm-cpu-runtime-execution` workflow implements layer 3 for Linux AMD64 CPU. It executes only on `main` or explicit dispatch. Pull requests validate the contract and tests without downloading or running the model.

Successful execution produces `a11oy.factory.runtime-execution/v1` evidence containing exact vLLM and PyTorch versions, qualified wheel digests, model revision and model-file digest, native extension path, CPU platform selection, generated token IDs, bounded timing measurements, environment inventory, and a canonical proof digest.

The proof intentionally reports `production_runtime_certified: false`.
