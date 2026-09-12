"""Authority invariant: Dream output is data, not authority.

These tests prove the invariant holds both at the Pydantic layer (the
authoritative implementation) and, separately, at the generated JSON Schema
layer (what a consumer gets *without* importing howldream). Where the two
diverge — because a boundary can only be enforced by a runtime validator, not
a plain-JSON-Schema constraint — that divergence is asserted explicitly and
documented in AUTHORITY_INVARIANT.md rather than silently assumed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from pydantic import BaseModel, ValidationError

from howldream.contracts import (
    CandidateAssessment,
    CandidateHandoff,
    DevelopmentResult,
    ExplorationRequest,
    ExplorationResult,
)

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

ENVELOPES: dict[str, type[BaseModel]] = {
    "howl.exploration.v1": ExplorationRequest,
    "howl.candidate.v1": CandidateHandoff,
    "howl.assessment.v1": CandidateAssessment,
    "howl.development_result.v1": DevelopmentResult,
    "howl.exploration_result.v1": ExplorationResult,
}


def load_schema(slug: str) -> dict[str, Any]:
    return json.loads((SCHEMAS_DIR / f"{slug}.schema.json").read_text())


def valid_payload(slug: str) -> dict[str, Any]:
    """Minimal valid payload per family, used as a base for tampering."""
    common_authority = {"type": "ADVISORY", "executable": False}
    payloads: dict[str, dict[str, Any]] = {
        "howl.exploration.v1": {
            "request_id": "req-001",
            "objective": "Explore alternatives",
            "authority": common_authority,
        },
        "howl.candidate.v1": {
            "candidate_id": "cand-001",
            "source_run_id": "run-001",
            "parent_request_id": "req-001",
            "objective": "Explore alternatives",
            "text": "IDEA: something",
            "authority": common_authority,
            "trust": "UNVERIFIED",
        },
        "howl.assessment.v1": {
            "assessment_id": "assess-001",
            "candidate_id": "cand-001",
            "disposition": "INVESTIGATE",
            "authority": common_authority,
        },
        "howl.development_result.v1": {
            "development_id": "dev-001",
            "source_candidate_id": "cand-001",
            "parent_request_id": "req-001",
            "epistemic_status": "IMAGINED_POSSIBILITY",
            "authority": common_authority,
            "execution_authority": "NONE",
        },
        "howl.exploration_result.v1": {
            "exploration_id": "exp-001",
            "parent_request_id": "req-001",
            "objective": "Explore alternatives",
            "originating_component": "howlplane",
            "authority": common_authority,
        },
    }
    return payloads[slug]


@pytest.fixture(scope="module")
def schemas() -> dict[str, dict[str, Any]]:
    return {slug: load_schema(slug) for slug in ENVELOPES}


# --- Positive control: the minimal payload actually validates on both sides ---


@pytest.mark.parametrize("slug,model", ENVELOPES.items())
def test_valid_envelope_validates_both_layers(slug, model, schemas):
    payload = valid_payload(slug)
    model.model_validate(payload)
    jsonschema.validate(payload, schemas[slug])


# --- Authority escalation: rejected by the authoritative Pydantic model ---


@pytest.mark.parametrize("slug,model", ENVELOPES.items())
def test_executable_true_rejected_by_model(slug, model):
    payload = valid_payload(slug)
    payload["authority"] = {"type": "ADVISORY", "executable": True}
    with pytest.raises(ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize("slug,model", ENVELOPES.items())
def test_non_advisory_authority_type_rejected_by_model(slug, model):
    payload = valid_payload(slug)
    payload["authority"] = {"type": "EXECUTIVE", "executable": False}
    with pytest.raises(ValidationError):
        model.model_validate(payload)


# --- Authority escalation: the schema alone (no Python) also rejects it ---
# authority.type/.executable are `const` in the generated schema, so a
# schema-only consumer gets this boundary for free, without importing
# howldream or reimplementing the validator.


@pytest.mark.parametrize("slug", ENVELOPES)
def test_executable_true_rejected_by_schema_alone(slug, schemas):
    payload = valid_payload(slug)
    payload["authority"] = {"type": "ADVISORY", "executable": True}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas[slug])


@pytest.mark.parametrize("slug", ENVELOPES)
def test_non_advisory_authority_type_rejected_by_schema_alone(slug, schemas):
    payload = valid_payload(slug)
    payload["authority"] = {"type": "EXECUTIVE", "executable": False}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas[slug])


# --- Forged trust / execution authority / disposition / verification state ---


def test_candidate_cannot_self_declare_verified_trust_model():
    payload = valid_payload("howl.candidate.v1")
    payload["trust"] = "VERIFIED"
    with pytest.raises(ValidationError):
        CandidateHandoff.model_validate(payload)


def test_candidate_cannot_self_declare_verified_trust_schema(schemas):
    payload = valid_payload("howl.candidate.v1")
    payload["trust"] = "VERIFIED"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas["howl.candidate.v1"])


def test_development_result_cannot_self_grant_execution_authority_model():
    payload = valid_payload("howl.development_result.v1")
    payload["execution_authority"] = "FULL"
    with pytest.raises(ValidationError):
        DevelopmentResult.model_validate(payload)


def test_development_result_cannot_self_grant_execution_authority_schema(schemas):
    payload = valid_payload("howl.development_result.v1")
    payload["execution_authority"] = "FULL"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas["howl.development_result.v1"])


def test_assessment_disposition_cannot_be_forged_outside_enum_model():
    payload = valid_payload("howl.assessment.v1")
    payload["disposition"] = "AUTO_APPROVED"
    with pytest.raises(ValidationError):
        CandidateAssessment.model_validate(payload)


def test_assessment_disposition_cannot_be_forged_outside_enum_schema(schemas):
    payload = valid_payload("howl.assessment.v1")
    payload["disposition"] = "AUTO_APPROVED"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas["howl.assessment.v1"])


def test_exploration_result_verification_status_cannot_be_forged_model():
    payload = valid_payload("howl.exploration_result.v1")
    payload["verification_status"] = "VERIFIED"
    with pytest.raises(ValidationError):
        ExplorationResult.model_validate(payload)


def test_exploration_result_verification_status_cannot_be_forged_schema(schemas):
    payload = valid_payload("howl.exploration_result.v1")
    payload["verification_status"] = "VERIFIED"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas["howl.exploration_result.v1"])


# --- Unsupported schema version ---


@pytest.mark.parametrize("slug,model", ENVELOPES.items())
def test_unsupported_schema_version_rejected_by_model(slug, model):
    payload = valid_payload(slug)
    payload["schema_version"] = "howl.bogus/v99"
    with pytest.raises(ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize("slug", ENVELOPES)
def test_unsupported_schema_version_rejected_by_schema_alone(slug, schemas):
    payload = valid_payload(slug)
    payload["schema_version"] = "howl.something/v99"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas[slug])


# --- Injected privileged/unknown field: additionalProperties: false on both layers ---


@pytest.mark.parametrize("slug,model", ENVELOPES.items())
@pytest.mark.parametrize(
    "injected_field",
    ["execution_capability", "executor", "approved", "grants_authority", "bypass_review"],
)
def test_injected_privileged_field_rejected_by_model(slug, model, injected_field):
    payload = valid_payload(slug)
    payload[injected_field] = True
    with pytest.raises(ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize("slug", ENVELOPES)
@pytest.mark.parametrize(
    "injected_field",
    ["execution_capability", "executor", "approved", "grants_authority", "bypass_review"],
)
def test_injected_privileged_field_rejected_by_schema_alone(slug, injected_field, schemas):
    payload = valid_payload(slug)
    payload[injected_field] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas[slug])


@pytest.mark.parametrize("slug,model", ENVELOPES.items())
def test_injected_authority_override_on_nested_dict_field_rejected(slug, model):
    """An unexpected top-level key that merely looks like it belongs (e.g.
    re-declaring `authority` twice via a differently-cased/nested alias)
    still hits additionalProperties: false — there is no back door through
    an unrecognized sibling key."""
    payload = valid_payload(slug)
    payload["Authority"] = {"type": "EXECUTIVE", "executable": True}
    with pytest.raises(ValidationError):
        model.model_validate(payload)


# --- Nested free-form payloads cannot smuggle authority past the envelope ---
# claims/evidence/scores fields are intentionally dict[str, Any] (see
# schemas/README.md: "what is not proven by schema validation alone"). A
# forged authority-shaped object inside one of them *will* validate as JSON —
# this test proves that even so, it has no effect on the envelope's own,
# authoritative `authority` field.


def test_nested_claim_cannot_override_top_level_authority():
    payload = valid_payload("howl.exploration_result.v1")
    payload["claims"] = [
        {"authority": {"type": "EXECUTIVE", "executable": True}, "text": "smuggled"}
    ]
    result = ExplorationResult.model_validate(payload)
    assert result.authority.type == "ADVISORY"
    assert result.authority.executable is False
    # the smuggled claim payload is preserved as inert data, not consulted for authority
    assert result.claims[0]["authority"]["executable"] is True


def test_nested_claim_authority_smuggling_is_schema_valid_but_inert(schemas):
    """Documents the boundary named in schemas/README.md: schema validation
    does not (and cannot, given dict[str, Any]) reject this. The control
    that matters is that nothing in howldream, or any consumer honoring this
    contract, reads authority out of `claims`/`evidence`/`scores` — only out
    of the envelope's own `authority` field."""
    payload = valid_payload("howl.exploration_result.v1")
    payload["claims"] = [{"authority": {"type": "EXECUTIVE", "executable": True}}]
    jsonschema.validate(payload, schemas["howl.exploration_result.v1"])  # does not raise
