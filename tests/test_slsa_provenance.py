"""Tests for a11oy_factory.slsa_provenance (SLSA absorb). Stdlib only."""
from __future__ import annotations

from a11oy_factory.slsa_provenance import (
    BuildDefinition,
    Material,
    ProvenanceError,
    RunDetails,
    make_record,
    validate_record,
)


def _expect_provenance_error(fn, *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
    except ProvenanceError:
        return
    raise AssertionError("expected ProvenanceError")


def _definition() -> BuildDefinition:
    return BuildDefinition(
        build_type="https://szl.example/buildtypes/estate-card/v1",
        builder="https://github.com/szl-holdings/a11oy-factory/.github/workflows/build.yml@refs/heads/main",
        invocation={"ref": "refs/heads/main"},
        materials=[
            Material(uri="git+https://github.com/szl-holdings/a11oy-factory", sha256="a" * 64),
            Material(uri="pkg:npm/left-pad@1.3.0", sha256="b" * 64),
        ],
    )


def test_valid_record_renders_and_validates():
    rec = make_record(_definition(), RunDetails(builder_version="1.2.3", metadata={"run_id": "42"}))
    assert rec["status"] == "PROPOSAL_ONLY"
    assert rec["not"] == ["signed", "verified", "attestation"]
    validate_record(rec)


def test_bad_build_type_rejected():
    _expect_provenance_error(
        make_record,
        BuildDefinition(build_type="not-a-uri", builder="b"),
        RunDetails(builder_version="1"),
    )


def test_bad_material_digest_rejected():
    _expect_provenance_error(
        make_record,
        BuildDefinition(
            build_type="https://x/v1",
            builder="b",
            materials=[Material(uri="m", sha256="deadbeef")],
        ),
        RunDetails(builder_version="1"),
    )


def test_missing_builder_version_rejected():
    _expect_provenance_error(make_record, _definition(), RunDetails(builder_version=""))


def test_validate_record_rejects_signed_claim():
    rec = make_record(_definition(), RunDetails(builder_version="1"))
    bad = dict(rec, status="SIGNED")
    _expect_provenance_error(validate_record, bad)


def test_validate_record_rejects_bad_digest():
    rec = make_record(_definition(), RunDetails(builder_version="1"))
    rec["buildDefinition"]["resolvedDependencies"][0]["digest"]["sha256"] = "ffff"
    _expect_provenance_error(validate_record, rec)
