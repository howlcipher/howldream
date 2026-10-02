"""Lossless advisory exports and scoped reviews; no generated assertion becomes evidence."""

from copy import deepcopy
from pathlib import Path

from howldream.artifacts import load_run
from howldream.contracts import CandidateHandoff, Provenance


def export_candidate(run_path: Path, candidate_id: str) -> CandidateHandoff:
    artifacts = load_run(run_path)
    unit = next(
        (u for u in artifacts.get("discovery", {}).get("units", []) if u["id"] == candidate_id),
        None,
    )
    if unit:
        from howldream.verification import extract

        parent = export_candidate(run_path, unit["candidate_id"])
        value = parent.model_dump()
        value.update(
            candidate_id=unit["id"],
            text=unit["text"],
            claims=extract(unit["text"], unit["id"]),
            verified_constraints=[],
        )
        provenance = value["provenance"]
        provenance["transformations"].append("idea_unit_selection")
        provenance.pop("verification", None)
        provenance.update(
            parent_candidate_id=parent.candidate_id,
            source_unit={k: unit[k] for k in ("id", "source_span", "source_hash", "cluster")},
            parent_verification_ref=f"verification.jsonl#candidate={parent.candidate_id}",
            unit_selection_scope=(
                "Single IDEA line; batch assumptions/unresolved issues retained without "
                "claim-specific association. Parent rejection/contradiction gates retained."
            ),
        )
        return CandidateHandoff.model_validate(value)
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
                "hard_constraints": experiment.get("constraints", []),
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

    for index, claim in enumerate(claims):
        claim.setdefault("candidate_id", candidate.candidate_id)
        claim.setdefault("id", f"{candidate.candidate_id}/claim/{index + 1}")
        if claim["candidate_id"] != candidate.candidate_id:
            raise ValueError("Claim candidate identity mismatch")
        if not isinstance(claim.get("kind"), str) or not isinstance(claim.get("text"), str):
            raise TypeError("Malformed structured claim: kind and text required")

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


def exploration_from_candidate(
    candidate: CandidateHandoff, *, objective=None, evidence=None, remote=False, max_calls=3
):
    """One canonical source, no promotion of speculative claims to evidence."""
    from uuid import uuid4

    from howldream.contracts import EvidenceRef, ExplorationBudget, ExplorationRequest

    return ExplorationRequest(
        request_id="candidate-" + uuid4().hex[:12],
        parent_run_id=candidate.source_run_id,
        objective=objective
        or "Challenge assumptions and identify falsifiable risks for: " + candidate.objective,
        originating_component="howlcreate"
        if candidate.provenance.producer_component == "howlcreate"
        else "howldream",
        constraints=list(candidate.provenance.model_extra.get("hard_constraints", []))
        if candidate.provenance.model_extra
        else [],
        source_candidates=[candidate],
        purpose="verification",
        evidence_refs=[EvidenceRef.model_validate(e.model_dump()) for e in (evidence or [])],
        budget=ExplorationBudget(
            max_calls=max_calls,
            max_candidates=2,
            provider_allowlist=["command"] if remote else ["mock"],
            local_only=not remote,
            forbid_local_inference=True,
        ),
        provenance=Provenance.model_validate(
            {
                "producer_component": "howldream",
                "transformations": ["candidate_to_exploration"],
                "source_candidate_id": candidate.candidate_id,
            }
        ),
    )
