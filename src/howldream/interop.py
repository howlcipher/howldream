"""Lossless advisory exports and scoped reviews; no generated assertion becomes evidence."""

from copy import deepcopy
from pathlib import Path

from howldream.artifacts import load_run
from howldream.contracts import CandidateHandoff, Provenance


def export_candidate(run_path: Path, candidate_id: str) -> CandidateHandoff:
    artifacts = load_run(run_path)
    if (run_path / "exploration_envelope.json").exists():
        import json

        envelope = json.loads((run_path / "exploration_envelope.json").read_text())
        for value in envelope["candidates"]:
            if value["candidate_id"] == candidate_id:
                return CandidateHandoff.model_validate(value)
    rows = artifacts["baseline"] + artifacts["candidates"]
    row = next((value for value in rows if value["id"] == candidate_id), None)
    if row is None:
        raise ValueError("candidate ID not present in run")
    claims = [value for value in artifacts["claims"] if value["candidate_id"] == candidate_id]
    checks = [value for value in artifacts["verification"] if value["candidate_id"] == candidate_id]
    supported = {value["claim_id"] for value in checks if value["status"] == "SUPPORTED"}
    experiment = artifacts["experiment"]
    return CandidateHandoff(
        candidate_id=candidate_id,
        source_run_id=run_path.name,
        parent_request_id=run_path.name,
        objective=experiment["objective"],
        text=row["text"],
        condition=row["condition"],
        claims=claims,
        evidence_refs=[value["id"] for value in experiment["evidence"]],
        assumptions=[value["text"] for value in claims if value["kind"] == "ASSUMPTION"],
        unresolved_issues=[value["text"] for value in claims if value["id"] not in supported],
        verified_constraints=[
            value["text"]
            for value in claims
            if value["id"] in supported and value.get("kind") in {"FACT", "CALC"}
        ],
        provenance=Provenance.model_validate(
            {
                "producer_component": "howldream",
                "run_id": run_path.name,
                "observation_kind": "SIMULATED"
                if (row.get("execution") or {}).get("mocked")
                else "EXTERNALLY_OBSERVED",
                "transformations": ["run_candidate_export"],
                "source_candidate": deepcopy(row),
                "verification": checks,
                "execution": row.get("execution"),
            }
        ),
    )


def review_candidate(candidate: CandidateHandoff, evidence):
    """Return a descendant review with scoped checks, preserving the complete original."""
    from howldream.verification import extract, extract_natural, verify

    original = candidate.model_dump()

    # 1. Consume structured claims if present,
    # otherwise extract reviewable claims from natural language
    if candidate.claims:
        claims = deepcopy(candidate.claims)
        claims_origin = "SOURCE_STRUCTURED"
    else:
        claims = extract_natural(candidate.text, candidate.candidate_id)
        if not claims:
            claims = extract(candidate.text, candidate.candidate_id)
        for cl in claims:
            cl["origin"] = "NATURAL_EXTRACTED"
            cl.setdefault("extractor", "claim_pipeline/v2")
        claims_origin = "NATURAL_EXTRACTED"

    # 2. Scoped verification against supplied evidence only
    checks = verify(claims, evidence)

    # 3. Descendant review envelope with provenance
    value = deepcopy(original)
    prov = value.setdefault("provenance", {})
    transformations = prov.setdefault("transformations", [])
    transformations.append("howldream_scoped_review")
    prov["source_candidate"] = original
    prov["review"] = {
        "producer_component": "howldream",
        "checks": checks,
        "claims_origin": claims_origin,
    }
    value["claims"] = claims
    # Review is not authorship and does not replace source claims or verification metadata.
    return CandidateHandoff.model_validate(value)
