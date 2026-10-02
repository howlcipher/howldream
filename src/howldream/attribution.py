"""Evidence-backed chronology auditing; never rewrites a contribution report."""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, model_validator

from howldream.contracts import StrictModel
from howldream.verification import evidence_echo

Category = Literal[
    "PREEXISTING",
    "HOWL_ORIGINATED",
    "HOWL_REFINED",
    "HOWL_CHALLENGED",
    "HOWL_VALIDATED",
    "HOWL_INSPIRED_TEST",
    "HOWL_NO_EFFECT",
]


class Entry(StrictModel):
    id: str = Field(min_length=1)
    recorded_at: str
    concept: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    concept_id: str | None = None
    classification: Category | None = None

    @model_validator(mode="after")
    def timestamp(self):
        if datetime.fromisoformat(self.recorded_at).tzinfo is None:
            raise ValueError("chronology requires timezone-aware timestamps")
        return self


class ContributionClaim(Entry):
    classification: Category


class AttributionLedger(StrictModel):
    schema_version: Literal["howl.attribution_audit/v1"]
    baseline: list[Entry]
    pre_howl_design: list[Entry] = Field(default_factory=list)
    howl_outputs: list[Entry]
    decisions: list[Entry] = Field(default_factory=list)
    final_claims: list[ContributionClaim]


def audit_attribution(value):
    ledger = AttributionLedger.model_validate(value)
    conflicts: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    prior = ledger.baseline + ledger.pre_howl_design
    for claim in ledger.decisions + ledger.final_claims:
        if claim.classification != "HOWL_ORIGINATED":
            continue

        def matching(entry, claim=claim):
            return (
                claim.concept_id is not None and claim.concept_id == entry.concept_id
            ) or evidence_echo(claim.concept, entry.concept)

        outputs = [entry for entry in ledger.howl_outputs if matching(entry)]
        if not outputs:
            unresolved.append({"claim_id": claim.id, "code": "MISSING_HOWL_ORIGIN_EVIDENCE"})
        earliest = min(
            (datetime.fromisoformat(entry.recorded_at) for entry in outputs),
            default=None,
        )
        claim_time = datetime.fromisoformat(claim.recorded_at)
        if earliest is not None and earliest > claim_time:
            unresolved.append(
                {
                    "claim_id": claim.id,
                    "code": "HOWL_ORIGIN_AFTER_ATTRIBUTION",
                    "source_refs": [entry.source_ref for entry in outputs],
                }
            )
        for entry in prior:
            if matching(entry) and datetime.fromisoformat(entry.recorded_at) <= (
                earliest or claim_time
            ):
                conflicts.append(
                    {
                        "code": "ATTRIBUTION_CONFLICT",
                        "claim_id": claim.id,
                        "recommended_classification": "PREEXISTING",
                        "baseline_id": entry.id,
                        "baseline_ref": entry.source_ref,
                        "baseline_recorded_at": entry.recorded_at,
                        "howl_first_recorded_at": earliest.isoformat()
                        if earliest is not None
                        else None,
                        "match_method": "concept_id_or_conservative_lexical_overlap",
                    }
                )
    return {
        "schema_version": "howl.attribution_audit_result/v1",
        "conflicts": conflicts,
        "unresolved": unresolved,
        "authority": "ADVISORY",
        "limitations": [
            "Timestamps and source references are supplied, not independently authenticated.",
            "Semantic paraphrases need stable concept IDs or human review; absence is not novelty.",
        ],
    }
