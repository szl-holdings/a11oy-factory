"""Deterministic, fail-closed AI distribution compiler.

The public facade turns a declarative catalog and profile into an immutable
lock, build plan, SPDX SBOM, SLSA provenance statement, and an A11oy receipt.
Metadata verification never implies runtime certification.
"""

from .distribution_common import (
    BUNDLE_BUILD_TYPE,
    CATALOG_SCHEMA,
    GENESIS,
    IN_TOTO_STATEMENT,
    LOCK_SCHEMA,
    PLAN_SCHEMA,
    PROFILE_SCHEMA,
    RECEIPT_SCHEMA,
    SLSA_PREDICATE,
    VERIFY_SCHEMA,
    FactoryError,
    canonical_bytes,
    catalog_summary,
    digest_json,
    read_json,
    validate_catalog,
    validate_profile,
)
from .distribution_evidence import (
    build_plan,
    generate_provenance,
    generate_spdx,
    verify_distribution,
    write_bundle,
)
from .distribution_materialize import materialize_artifacts
from .distribution_resolver import resolve_distribution

__all__ = [
    "BUNDLE_BUILD_TYPE",
    "CATALOG_SCHEMA",
    "GENESIS",
    "IN_TOTO_STATEMENT",
    "LOCK_SCHEMA",
    "PLAN_SCHEMA",
    "PROFILE_SCHEMA",
    "RECEIPT_SCHEMA",
    "SLSA_PREDICATE",
    "VERIFY_SCHEMA",
    "FactoryError",
    "build_plan",
    "canonical_bytes",
    "catalog_summary",
    "digest_json",
    "generate_provenance",
    "generate_spdx",
    "materialize_artifacts",
    "read_json",
    "resolve_distribution",
    "validate_catalog",
    "validate_profile",
    "verify_distribution",
    "write_bundle",
]
