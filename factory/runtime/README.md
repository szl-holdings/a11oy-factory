# A11oy Factory runtime proofs

The distribution compiler proves metadata integrity. Artifact qualification proves exact upstream bytes. Runtime execution proofs add a narrower third layer: a pinned runtime must actually load its native extension and generate tokens from a pinned model revision on a named target.

## CPU AMD64 vLLM smoke

`vllm-cpu-amd64-smoke.json` binds:

- the `pytorch-cpu-amd64` wheel in `factory/catalog.json`;
- the `vllm-cpu-amd64` wheel in `factory/catalog.json`;
- `HuggingFaceTB/SmolLM2-135M-Instruct` at an immutable Git revision;
- CPU-only execution with `trust_remote_code=false`;
- deterministic sampling parameters and a bounded context;
- a machine-readable runtime proof retained by GitHub Actions.

The proof requires the verified wheel bytes to remain unchanged through installation, imports the native `vllm._C` extension, confirms that vLLM selected its CPU platform, hashes the pinned model file, and requires at least one generated token.

This is a scoped execution proof for one GitHub-hosted Linux AMD64 CPU environment. It does not certify every CPU, operating system, accelerator, model, workload, or production service configuration. `production_runtime_certified` therefore remains `false`.
