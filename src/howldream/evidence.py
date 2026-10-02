"""Declared validation provenance and conservative, scoped report-language auditing.

Declarations describe supplied artifacts; they do not authenticate external reality.
Passing a fixture never upgrades its source type or establishes operational efficacy.
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceType = Literal[
    "UNCLASSIFIED",
    "EXTERNAL_GROUND_TRUTH",
    "EXTERNAL_OBSERVATION",
    "HISTORICAL_DATASET",
    "DERIVED_FROM_EXTERNAL_DATA",
    "MODEL_INVARIANT",
    "SYNTHETIC_FIXTURE",
    "OPERATOR_EXPECTATION",
    "SIMULATION_EXPECTATION",
    "MODEL_SELF_CONSISTENCY",
]
EXTERNAL = {
    "EXTERNAL_GROUND_TRUTH",
    "EXTERNAL_OBSERVATION",
    "HISTORICAL_DATASET",
    "DERIVED_FROM_EXTERNAL_DATA",
}


class EvidenceProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source_type: SourceType = "UNCLASSIFIED"
    produced_by: str = Field(default="unknown", min_length=1, max_length=500)
    source_ref: str = Field(default="", max_length=2000)
    independent_of_implementation: bool = False
    represents_observed_reality: bool = False

    @model_validator(mode="after")
    def source_declarations(self):
        if self.source_type in EXTERNAL and (not self.source_ref or self.produced_by == "unknown"):
            raise ValueError("External evidence requires source_ref and produced_by")
        if self.source_type == "EXTERNAL_GROUND_TRUTH" and not (
            self.independent_of_implementation and self.represents_observed_reality
        ):
            raise ValueError("External ground truth requires independent observed data")
        if (
            self.source_type
            in {
                "SYNTHETIC_FIXTURE",
                "OPERATOR_EXPECTATION",
                "SIMULATION_EXPECTATION",
                "MODEL_SELF_CONSISTENCY",
            }
            and self.represents_observed_reality
        ):
            raise ValueError(
                "Authored expectations/self-consistency cannot declare observed reality"
            )
        return self


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1, max_length=200)
    provenance: EvidenceProvenance = Field(default_factory=EvidenceProvenance)
    expected_value_origin: str = Field(min_length=1, max_length=2000)
    scope: str = Field(min_length=1, max_length=5000)
    outcome: Literal["PASS", "FAIL", "NOT_RUN"]
    artifact_ref: str = Field(min_length=1, max_length=2000)
    holdout: bool = False
    independent_benchmark: bool = False
    prospective: bool = False
    causal_comparison: bool = False
    measured_metrics: list[str] = Field(default_factory=list, max_length=50)
    limitations: list[str] = Field(default_factory=list, max_length=50)

    def maturity(self) -> dict:
        p = self.provenance
        level, label = 0, "untested hypothesis"
        if self.outcome == "PASS" and p.source_type != "UNCLASSIFIED":
            level, label = 1, "controlled validation"
            if p.source_type in EXTERNAL and p.represents_observed_reality:
                level, label = 2, "retrospective observed-data evaluation"
                if p.independent_of_implementation and self.independent_benchmark:
                    level, label = 3, "independent external benchmark"
                    if self.prospective:
                        level, label = 4, "prospective operational evaluation"
        return {"level": level, "label": label, "basis": "declared artifacts, not authentication"}


def validation_requirements(product_kind: str) -> list[str]:
    """Prototype checklists, not mandatory authority gates."""
    requirements = {
        "decision": ["historical decisions", "independent outcomes", "counterfactual limitations"],
        "forecast": ["holdout data", "external benchmark", "calibration/error measurement"],
        "detector": ["known positives", "known negatives", "synthetic controls", "population test"],
        "simulation": ["independent observed measurements", "calibration", "model limitations"],
    }
    if product_kind not in requirements:
        raise ValueError("Unknown product kind")
    return requirements[product_kind]


class ClaimSupport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    claim: str = Field(min_length=1, max_length=10000)
    validation_ids: list[str] = Field(default_factory=list, max_length=100)


class ReportEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    validations: list[ValidationResult] = Field(default_factory=list, max_length=500)
    bindings: list[ClaimSupport] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def known_references(self):
        ids = [v.id for v in self.validations]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate validation IDs")
        if any(ref not in ids for b in self.bindings for ref in b.validation_ids):
            raise ValueError("Unknown supporting validation ID")
        return self


SENSITIVE = re.compile(
    r"\b(production[- ]grade|proven|historically validated|historically proven|"
    r"beats? (?:the )?baseline|outperforms?|best|accurate|real[- ]world validated|"
    r"validated against (?:real[- ]world |)historical|Statcast confirms|improve[s]? wins)\b",
    re.IGNORECASE,
)


def audit_report(text: str, evidence: ReportEvidence) -> dict:
    """Exact claim bindings prevent unrelated good evidence laundering other claims.

    This catches common exaggerations, not entailment or all possible paraphrases.
    Even a clean result requires human assessment of measurements and scope.
    """
    by_id = {v.id: v for v in evidence.validations}
    findings = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        if not SENSITIVE.search(sentence):
            continue
        binding = next((b for b in evidence.bindings if b.claim == sentence), None)
        validations = [by_id[i] for i in binding.validation_ids] if binding else []
        passed = [v for v in validations if v.outcome == "PASS"]
        observed = [
            v
            for v in passed
            if v.provenance.source_type in EXTERNAL
            and v.provenance.represents_observed_reality
            and v.provenance.independent_of_implementation
        ]
        lower = sentence.lower()
        reasons = []
        if not passed:
            reasons.append("No explicitly bound passing validation")
        if not observed:
            reasons.append("No independent observed data for empirical language")
        if re.search(r"production[- ]grade|\bproven\b|\bbest\b", lower):
            reasons.append("Absolute readiness/superiority requires a scoped human review")
        if re.search(r"beats?|outperform|improve.*wins", lower) and not any(
            v.independent_benchmark and v.measured_metrics for v in observed
        ):
            reasons.append("No measured independent baseline comparison")
        if "wins" in lower and not any(v.causal_comparison for v in observed):
            reasons.append("Retrospective association is not a causal strategy benefit")
        if "accurate" in lower and not any(v.holdout and v.measured_metrics for v in observed):
            reasons.append("No holdout error/calibration measurement")
        if "statcast" in lower and not any(
            "statcast" in v.provenance.source_ref.lower() for v in observed
        ):
            reasons.append("No bound Statcast observation artifact")
        if "real-world validated" in lower and not any(v.prospective for v in observed):
            reasons.append("No prospective operational evaluation")
        if reasons:
            types = sorted({v.provenance.source_type for v in validations})
            wording = (
                "Passed controlled synthetic validation within the declared test scope."
                if "SYNTHETIC_FIXTURE" in types
                else "Consistent with stated model assumptions in controlled checks."
                if set(types) & {"MODEL_SELF_CONSISTENCY", "MODEL_INVARIANT"}
                else "Matched operator-authored expectations; external accuracy remains untested."
                if "OPERATOR_EXPECTATION" in types
                else "Retrospective evaluation within the declared dataset scope."
                if observed
                else "Empirical validation remains unestablished."
            )
            findings.append(
                {
                    "code": "CLAIM_EVIDENCE_MISMATCH",
                    "claim": sentence,
                    "supporting_evidence": [v.model_dump() for v in validations],
                    "evidence_type": types or ["UNCLASSIFIED"],
                    "why_insufficient": reasons,
                    "suggested_narrower_wording": wording,
                }
            )
    return {
        "findings": findings,
        "audit_type": "ADVISORY_HEURISTIC",
        "limitations": [
            "Exact scope bindings required",
            "No external authentication or entailment",
        ],
    }
