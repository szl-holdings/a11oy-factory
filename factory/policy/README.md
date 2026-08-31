# A11oy Factory assurance channels

The factory evaluates evidence instead of promoting by label alone.

## Candidate

The candidate channel requires a complete current OSV query, exact download SHA-256 evidence for the isolated runtime environment, at least license-file evidence, and a successful scoped runtime-execution proof. Critical vulnerability matches block candidate admission. Candidate does not require a production signature and does not imply production certification.

## Stable

The stable channel adds stricter licensing, blocks high and critical vulnerability matches as well as unknown severity, and requires a real cryptographic signature. `UNSIGNED-honest` cannot satisfy this policy. Stable therefore remains fail closed until signing and the measured policy conditions hold.

A blocked channel is a valid result. The assurance workflow is successful when it executes the observation pipeline, verifies all evidence digests, and emits reproducible verdicts. It does not turn red merely because a channel correctly refuses promotion.

The scheduled workflow re-runs the OSV query every Monday and binds its verdicts to the latest successful CPU runtime proof.
