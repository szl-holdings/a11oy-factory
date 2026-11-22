# Domain Leader Study — a11oy-factory (governed AI distribution)

OUROBOROS phase-3, cohort-01 tranche-2. PROPOSE-ONLY study card: documentation only, no production change in this PR.

## Domain leaders studied
| Leader | What they have | Key sources |
| --- | --- | --- |
| SLSA framework (OpenSSF) | Build provenance spec v2.0 (BuildDefinition / RunDetails), artifact-verification policy model, build-level ladder L1-L3 | slsa.dev/spec/latest/build-provenance; slsa.dev/spec/latest/verifying-artifacts |
| slsa-framework/slsa (GitHub) | Reference verifier, provenance generators per ecosystem, in-toto attestation formats | github.com/slsa-framework/slsa |

## What the leaders do better
- Provenance is a first-class, independently verifiable artifact: the consumer re-derives trust from (buildType, externalParameters, builder identity) recorded at build time, not from the builder's say-so.
- Verification is expectation-based: a policy lists allowed buildTypes/builders; anything outside the list fails closed. Same shape as our receipt gates.
- Levels let consumers state "built at L2" without trusting the producer's process, only its signed provenance.

## Absorb actions (proposed, NOT implemented in this PR)
- [ ] Add a provenance block to factory release receipts: sha256 of artifact + builder id + buildType + externalParameters, SLSA-shaped keys.
- [ ] Add a verify step that fails the gate when provenance fields are missing or builder id is not on the allow-list (fail-closed, never-manufacture-green).
- [ ] Document the factory's current equivalent of each SLSA build level (today: L1-ish signed receipts; target: L2 reproducible builder digest).
- [ ] Align receipt JSON naming with SLSA BuildDefinition/RunDetails so external verifiers can parse our receipts directly.

## Sources
- SLSA Build Provenance: https://slsa.dev/spec/latest/build-provenance
- SLSA Verifying Artifacts: https://slsa.dev/spec/latest/verifying-artifacts
- slsa-framework: https://github.com/slsa-framework/slsa
