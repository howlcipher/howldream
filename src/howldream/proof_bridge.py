"""Dream <-> Proof bridge: export a candidate's claims, import per-claim results.

Dream proposes; Proof challenges. Nothing here invents an acceptance requirement,
promotes a proposed verification plan to a check, calls a model, or touches the
network. A check exists in an exported bundle only when the candidate's own author
supplied one. Every claim keeps its own result on the way back, and INCONCLUSIVE is
never converted into REJECTED or accepted.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from howldream import __version__
from howldream.contracts import (
    CandidateAssessment,
    CandidateHandoff,
    ExplorationAuthority,
    Provenance,
)
from howldream.evidence import EXTERNAL
from howldream.schema import Evidence

BUNDLE_SCHEMA = "howl.claim_bundle/v1"
CATEGORIES = ("EMPIRICAL", "TECHNICAL", "HYPOTHESIS", "VALUE_JUDGMENT")
CLAIM_STATUSES = (
    "SUPPORTED",
    "REFUTED",
    "INCONCLUSIVE",
    "REQUIRES_EXTERNAL_VALIDATION",
    "ERROR",
)

_JUDGMENT = re.compile(
    r"\b(will|would|going to|expected to|likely|forecast\w*|predict\w*|should|best|worst|"
    r"better than|worth|promising|by (?:19|20)\d\d|next (?:year|decade))\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d")

PLANS = {
    "EMPIRICAL": [
        "compare against independent primary-source data",
        "record units, dates and methodology of every source",
    ],
    "TECHNICAL": ["author a deterministic experiment or executable check and supply it as a check"],
    "HYPOTHESIS": ["design an investigation and state what observation would refute it"],
    "VALUE_JUDGMENT": ["external validation: human judgment or prospective data"],
}


def authorship(candidate: CandidateHandoff) -> dict[str, Any]:
    """Who actually wrote this idea, from the candidate's own records. Never assumes Dream did."""
    extra = candidate.provenance.model_extra or {}
    origin = extra.get("origin")
    if isinstance(origin, dict) and origin.get("component"):
        return {
            "kind": "EXTERNAL_AUTHORED",
            "component": origin["component"],
            "provider": origin.get("provider"),
            "model": origin.get("model"),
        }
    execution = extra.get("execution") or (extra.get("source_candidate") or {}).get("execution")
    participation = extra.get("participation") or []
    first = participation[0] if participation else {}
    if isinstance(execution, dict) and execution.get("mocked"):
        return {
            "kind": "MOCK",
            "component": "fixture",
            "provider": execution.get("actual_provider"),
            "model": None,
            "note": "mock provider output; Dream did not generate it",
        }
    if first.get("operation") == "GENERATED" and first.get("inference_occurred"):
        return {
            "kind": "MODEL_GENERATED",
            "component": first.get("origin_component", "howldream"),
            "provider": first.get("origin_provider"),
            "model": first.get("origin_model"),
        }
    if first.get("origin_component") == "fixture":
        return {
            "kind": "SYNTHETIC_FIXTURE",
            "component": "fixture",
            "provider": None,
            "model": None,
        }
    return {
        "kind": "UNKNOWN",
        "component": None,
        "provider": None,
        "model": None,
        "note": "artifact carries no authorship records (legacy or hand-built)",
    }


def classify(claim: dict[str, Any]) -> tuple[str, str]:
    """(category, basis). An explicit category wins; otherwise a conservative heuristic."""
    explicit = claim.get("category")
    if explicit is not None:
        if explicit not in CATEGORIES:
            raise ValueError(f"claim category {explicit!r} is not one of {', '.join(CATEGORIES)}")
        return explicit, "explicit"
    text, kind = str(claim.get("text", "")), claim.get("kind")
    if kind == "ASSUMPTION":
        return "HYPOTHESIS", "heuristic"
    if kind == "CALC":
        return "TECHNICAL", "heuristic"
    if _JUDGMENT.search(text):
        return "VALUE_JUDGMENT", "heuristic"
    if _NUMBER.search(text) or kind in ("FACT", "CITE"):
        return "EMPIRICAL", "heuristic"
    return "HYPOTHESIS", "heuristic"


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._") or "evidence"


def _write_evidence(evidence: list[Evidence], out: Path) -> list[dict[str, Any]]:
    entries = []
    (out / "evidence").mkdir()
    for index, source in enumerate(evidence, start=1):
        body = json.dumps(
            {"id": source.id, "text": source.text, "facts": source.facts},
            sort_keys=True,
            indent=2,
        ).encode()
        relative = f"evidence/{index:03d}-{_safe(source.id)}.json"
        (out / relative).write_bytes(body)
        provenance = source.provenance
        entries.append(
            {
                "id": source.id,
                "path": relative,
                "sha256": hashlib.sha256(body).hexdigest(),
                "source_type": provenance.source_type,
                "produced_by": provenance.produced_by,
                "source_ref": provenance.source_ref,
                "independent": provenance.source_type in EXTERNAL
                and provenance.independent_of_implementation,
                "represents_observed_reality": provenance.represents_observed_reality,
                "published_at": source.facts.get("published_at")
                or source.facts.get("retrieved_at"),
            }
        )
    return entries


def _claims(candidate: CandidateHandoff) -> tuple[list[dict[str, Any]], str]:
    from howldream.verification import extract, extract_natural

    if candidate.claims:
        return [dict(c) for c in candidate.claims], "SOURCE_STRUCTURED"
    found = extract_natural(candidate.text, candidate.candidate_id) or extract(
        candidate.text, candidate.candidate_id
    )
    return found, "NATURAL_EXTRACTED"


def export_proof(
    candidate: CandidateHandoff, evidence: list[Evidence | dict], out: Path
) -> dict[str, Any]:
    """Write `claims.json` and its evidence files under `out`. Refuses a non-empty directory."""
    sources = [e if isinstance(e, Evidence) else Evidence.model_validate(e) for e in evidence]
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory {out} is not empty; refusing to overwrite")
    claims, origin = _claims(candidate)
    all_refs = [s.id for s in sources]
    rows = []
    for index, claim in enumerate(claims, start=1):
        category, basis = classify(claim)
        check = claim.get("check")
        falsification, falsification_basis = claim.get("falsification"), None
        if falsification:
            falsification_basis = "author"
        elif isinstance(check, dict) and check.get("type") == "fact_compare":
            falsification = (
                f"refuted if independent evidence reports {check.get('fact')} "
                f"not {check.get('op')} {check.get('expected')}"
            )
            falsification_basis = "derived_from_check"
        rows.append(
            {
                "claim_id": claim.get("id") or f"{candidate.candidate_id}/claim/{index}",
                "text": claim["text"],
                "source_kind": claim.get("kind"),
                "category": category,
                "category_basis": basis,
                "origin": claim.get("origin") or origin,
                "assumption": claim.get("kind") == "ASSUMPTION",
                "falsification": falsification,
                "falsification_basis": falsification_basis,
                "evidence_refs": list(claim.get("evidence_refs") or all_refs),
                "check": check,
                "verification_plan": {
                    "status": "PROPOSED",
                    "grounded": check is not None,
                    "methods": PLANS[category],
                    "note": "a proposed plan is not an acceptance test; only a supplied check "
                    "is evaluated",
                },
            }
        )
    for text in candidate.assumptions:
        rows.append(
            {
                "claim_id": f"{candidate.candidate_id}/assumption/{len(rows) + 1}",
                "text": text,
                "source_kind": "ASSUMPTION",
                "category": "HYPOTHESIS",
                "category_basis": "assumption",
                "origin": "SOURCE_STRUCTURED",
                "assumption": True,
                "falsification": None,
                "falsification_basis": None,
                "evidence_refs": all_refs,
                "check": None,
                "verification_plan": {
                    "status": "PROPOSED",
                    "grounded": False,
                    "methods": PLANS["HYPOTHESIS"],
                    "note": "a stated assumption stays unresolved",
                },
            }
        )
    out.mkdir(parents=True, exist_ok=True)
    document = {
        "schema": BUNDLE_SCHEMA,
        "candidate": {
            "candidate_id": candidate.candidate_id,
            "source_run_id": candidate.source_run_id,
            "parent_request_id": candidate.parent_request_id,
            "objective": candidate.objective,
            "text": candidate.text,
            "status": candidate.status,
            "trust": candidate.trust,
        },
        "authorship": authorship(candidate),
        "claims": rows,
        "evidence": _write_evidence(sources, out),
        "lineage": {
            "exported_by": "howldream",
            "exporter_version": __version__,
            "candidate_created_at": candidate.provenance.created_at,
            "candidate_sha256": hashlib.sha256(candidate.model_dump_json().encode()).hexdigest(),
        },
    }
    (out / "claims.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    return document


def import_proof(bundle_dir: Path, result: dict[str, Any]) -> CandidateAssessment:
    """Turn a `howlproof evaluate --json` result into a howl.assessment/v1, claim by claim."""
    raw = (bundle_dir / "claims.json").read_bytes()
    bundle = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    candidate = bundle["candidate"]
    checks = [
        c
        for c in result.get("checks", [])
        if str(c.get("check_id", "")).startswith("research.claims.")
    ]
    if not checks:
        raise ValueError("proof result has no research.claims checks; nothing was evaluated")
    gate = next((c for c in checks if c["check_id"] == "research.claims.bundle"), None)
    for check in checks:
        seen = (check.get("detail") or {}).get("bundle_sha256")
        if seen != digest:
            raise ValueError(
                "proof result was produced for a different claim bundle "
                f"(result {str(seen)[:12]}, bundle {digest[:12]})"
            )
    known = {c["claim_id"]: c for c in bundle["claims"]}
    verdicts: dict[str, dict[str, Any]] = {}
    for check in checks:
        detail = check.get("detail") or {}
        if "claim_status" not in detail:
            continue
        if detail["claim_id"] not in known:
            raise ValueError(f"proof result names claim {detail['claim_id']!r} not in the bundle")
        if detail["claim_status"] not in CLAIM_STATUSES:
            raise ValueError(f"unknown claim status {detail['claim_status']!r}")
        verdicts[detail["claim_id"]] = detail

    integrity_ok = gate is not None and gate.get("status") == "VERIFIED"
    rows: list[dict[str, Any]] = []
    statuses: dict[str, str] = {}
    for claim_id, claim in known.items():
        detail = verdicts.get(claim_id)
        statuses[claim_id] = detail["claim_status"] if detail else "NOT_ASSESSED"
        rows.append(
            {
                "kind": "proof_claim_result",
                "claim_id": claim_id,
                "claim_text": claim["text"],
                "category": claim["category"],
                "claim_origin": claim["origin"],
                "assumption": claim["assumption"],
                "claim_status": statuses[claim_id],
                "method": detail["method"] if detail else "none",
                "explanation": detail["explanation"] if detail else "no result returned",
                "evidence_considered": detail["evidence_considered"] if detail else [],
                "conflicts": detail["conflicts"] if detail else [],
                "not_checked": detail["not_checked"] if detail else [],
                "untrusted_flags": detail["untrusted_flags"] if detail else [],
            }
        )
    values = list(statuses.values())
    texts = {cid: c["text"] for cid, c in known.items()}
    contradictions = [texts[c] for c, s in statuses.items() if s == "REFUTED"]
    unresolved = [texts[c] for c, s in statuses.items() if s not in ("SUPPORTED", "REFUTED")]
    if values and all(v == "SUPPORTED" for v in values) and integrity_ok:
        disposition, confidence = "ACCEPT_FOR_DEVELOPMENT", "MEDIUM"
        reason = f"all {len(values)} claim(s) supported by independent evidence"
    elif values and all(v == "REFUTED" for v in values):
        disposition, confidence = "REJECT", "HIGH"
        reason = f"all {len(values)} claim(s) refuted"
    elif contradictions:
        disposition, confidence = "INVESTIGATE", "LOW"
        reason = f"{len(contradictions)} claim(s) refuted; {len(unresolved)} unresolved"
    else:
        disposition, confidence = "UNRESOLVED", "LOW"
        reason = f"{len(unresolved)} claim(s) remain unresolved"
    limitations = list(dict.fromkeys(result.get("limitations") or []))
    if not integrity_ok:
        limitations.append("evidence integrity check did not pass; acceptance withheld")
    limitations.append(
        "claim results hold only for the checks the candidate's author supplied; "
        "independence of evidence is as declared, not authenticated"
    )
    completed = result.get("completed_at") or result.get("started_at")
    key = json.dumps([digest, sorted(statuses.items())], sort_keys=True).encode()
    provenance: dict[str, Any] = {
        "run_id": candidate["source_run_id"],
        "producer_component": "howldream",
        "producer_version": __version__,
        "observation_kind": "DETERMINISTIC",
        "transformations": ["howlproof_claim_import"],
        "source_candidate_id": candidate["candidate_id"],
        "bundle_sha256": digest,
        "authorship": bundle["authorship"],
        "proof": {
            "run_id": result.get("run_id"),
            "version": result.get("version"),
            "verdict": result.get("verdict"),
            "deciding_rule": result.get("deciding_rule"),
            "started_at": result.get("started_at"),
            "completed_at": result.get("completed_at"),
            "unresolved_risks": result.get("unresolved_risks", []),
        },
        "claim_statuses": statuses,
    }
    if completed:
        provenance["created_at"] = completed
    return CandidateAssessment(
        schema_version="howl.assessment/v1",
        assessment_id=f"assess-proof-{hashlib.sha256(key).hexdigest()[:16]}",
        candidate_id=candidate["candidate_id"],
        disposition=disposition,  # type: ignore[arg-type]
        reason=reason,
        evidence=rows,
        unresolved_claims=unresolved,
        contradictions=contradictions,
        confidence=confidence,  # type: ignore[arg-type]
        limitations=limitations,
        authority=ExplorationAuthority(),
        provenance=Provenance.model_validate(provenance),
    )
