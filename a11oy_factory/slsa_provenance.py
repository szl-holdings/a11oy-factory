"""SLSA-style build provenance records (absorb implementation).

Absorbs, at schema level only (source card: docs/LEADERS-STUDY.md on
branch study/leader-cohort1-t2, leader-study PR a11oy-factory#112):
the SLSA framework's provenance shape -- BuildDefinition and
RunDetails (slsa-github, verifying-artifacts policy model). Anchor:
https://slsa.dev/spec/v1.0 ; https://github.com/slsa-framework/slsa

HONEST SCOPE: this module builds and validates plain data records.
It does NOT sign anything, verify any signature, attest any build, or
talk to a network. Signature binding and promotion remain owner-gated
per estate doctrine; every record it produces is labelled PROPOSAL_ONLY.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

SCHEMA = "szl.a11oy-factory.slsa-provenance/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceError(ValueError):
    """Raised when a provenance record fails validation."""


@dataclass
class Material:
    """A resolved input to the build, identified by digest."""
    uri: str
    sha256: str

    def validate(self) -> None:
        if not self.uri:
            raise ProvenanceError("material.uri required")
        if not SHA256_RE.match(self.sha256 or ""):
            raise ProvenanceError(f"material.sha256 must be 64 lowercase hex: {self.uri!r}")

    def to_dict(self) -> dict[str, Any]:
        return {"uri": self.uri, "digest": {"sha256": self.sha256}}


@dataclass
class BuildDefinition:
    """SLSA v1-style build definition (builder + parameters + materials)."""
    build_type: str
    builder: str
    invocation: dict[str, Any] = field(default_factory=dict)
    materials: list[Material] = field(default_factory=list)

    def validate(self) -> None:
        if not self.build_type or not self.build_type.startswith(("http://", "https://")):
            raise ProvenanceError("build_type must be a URI identifying the build type")
        if not self.builder:
            raise ProvenanceError("builder id required")
        for m in self.materials:
            m.validate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "buildType": self.build_type,
            "externalParameters": dict(self.invocation),
            "resolvedDependencies": [m.to_dict() for m in self.materials],
        }


@dataclass
class RunDetails:
    """SLSA v1-style run details (builder version + run metadata)."""
    builder_version: str
    metadata: dict[str, Any] = field(default_factory=dict)
    byproducts: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        if not self.builder_version:
            raise ProvenanceError("builder_version required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "builder": {"id": "", "version": self.builder_version},
            "metadata": dict(self.metadata),
            "byproducts": list(self.byproducts),
        }


def make_record(definition: BuildDefinition, details: RunDetails) -> dict[str, Any]:
    """Validate and render an unsigned, PROPOSAL_ONLY provenance record."""
    definition.validate()
    details.validate()
    return {
        "schema": SCHEMA,
        "status": "PROPOSAL_ONLY",
        "buildDefinition": definition.to_dict(),
        "runDetails": details.to_dict(),
        "not": ["signed", "verified", "attestation"],
        "signature_binding": "OWNER_GATED",
    }


def validate_record(record: dict[str, Any]) -> None:
    """Fail-closed validation of a rendered record."""
    if record.get("schema") != SCHEMA:
        raise ProvenanceError(f"schema must be {SCHEMA}")
    if record.get("status") != "PROPOSAL_ONLY":
        raise ProvenanceError("records produced here are PROPOSAL_ONLY; signed records are owner-gated")
    bd = record.get("buildDefinition") or {}
    if not str(bd.get("buildType") or "").startswith(("http://", "https://")):
        raise ProvenanceError("buildDefinition.buildType must be a URI")
    for dep in bd.get("resolvedDependencies", []):
        digest = (dep.get("digest") or {}).get("sha256") or ""
        if not SHA256_RE.match(digest):
            raise ProvenanceError(f"resolvedDependencies digest must be sha256 hex: {dep.get('uri')!r}")
    rd = record.get("runDetails") or {}
    if not ((rd.get("builder") or {}).get("version")):
        raise ProvenanceError("runDetails.builder.version required")
