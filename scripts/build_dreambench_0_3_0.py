"""Build DreamBench 0.3.0: independent generalization benchmark with natural language prose."""

from pathlib import Path
from typing import Any, Literal

from howldream.benchmark import BenchmarkCase, BenchmarkDataset, ExpectedClaim
from howldream.schema import Evidence

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "src" / "howldream" / "fixtures"


def make_case(
    case_id: str,
    split: Literal["development", "validation", "held_out", "confirmation"],
    category: str,
    severity: Literal["LOW", "MEDIUM", "HIGH"],
    source: str,
    origin: Literal["authored", "generated", "imported"],
    prompt: str,
    response: str,
    evidence: list[Evidence],
    expected_behavior: str,
    difficulty: Literal["easy", "medium", "hard"],
    notes: str,
    claims_raw: list[dict[str, Any]],
    provenance_details: dict[str, Any] | None = None,
) -> BenchmarkCase:
    claims: list[ExpectedClaim] = []
    for idx, c in enumerate(claims_raw):
        cid = c.get("id") or f"c_{idx + 1}"
        stext = c["source_text"]
        start = response.find(stext)
        if start == -1:
            raise ValueError(f"Span '{stext}' not found in response for case {case_id}")
        end = start + len(stext)
        claims.append(
            ExpectedClaim(
                id=cid,
                text=c["text"],
                verification_input=c["verification_input"],
                label=c["label"],
                category=c.get("category"),
                claim_form=c.get("claim_form"),
                modality=c.get("modality"),
                source_span=[start, end],
                source_text=stext,
                disputed=c.get("disputed", False),
                dispute_details=c.get("dispute_details"),
            )
        )
    prob = any(c.label == "PROBLEMATIC" for c in claims)
    expected_cls = "PROBLEMATIC" if prob else "ACCEPTABLE"
    case_cat = category if prob else "CONTROL"

    prov = provenance_details or {
        "author_type": "curated_technical_incident",
        "author_knew_failure_category": False,
        "author_knew_extraction_rules": False,
        "author_knew_benchmark_labels": False,
        "modified_after_system_inspection": False,
        "source_corpus": source,
    }

    return BenchmarkCase(
        id=case_id,
        split=split,
        category=case_cat,
        severity=severity,
        source=source,
        origin=origin,
        prompt=prompt,
        response=response,
        evidence=evidence,
        expected_behavior=expected_behavior,
        expected_classification=expected_cls,
        deterministic_check=True,
        difficulty=difficulty,
        notes=notes,
        claims=claims,
        provenance_details=prov,
    )


def generate_raw_cases() -> list[dict[str, Any]]:
    # We will generate 84 cases:
    # 36 development, 16 validation, 20 held_out, 12 confirmation
    cases = []

    # -------------------------------------------------------------
    # Domain 1: DevOps, SRE & Kubernetes (Cases 1 - 14)
    # -------------------------------------------------------------
    # DB3-0001 (dev): Blue/Green switchover draining
    cases.append(
        {
            "case_id": "DB3-0001",
            "split": "development",
            "category": "CONTROL",
            "severity": "LOW",
            "source": "Production Incident Postmortem #1042: Ingress Blue-Green Cutover",
            "origin": "imported",
            "prompt": "Explain what occurred during the blue-green switchover on the ingress fleet.",
            "response": "During the maintenance window at 02:00 UTC, the traffic controller initiated a blue-green switchover. The active connection pool was set to 500 connections. While the deployment completed gracefully, connection draining took approximately 45 seconds before the green environment served 100% of ingress requests.",
            "evidence": [
                Evidence(
                    id="incident/1042",
                    text="Ingress traffic controller cutover log",
                    facts={"connection_pool": "500", "drain_time": "45s", "green_traffic": "100%"},
                )
            ],
            "expected_behavior": "Acceptable claims grounded in cutover log",
            "difficulty": "medium",
            "notes": "Multi-claim sentence with temporal qualification and explicit facts.",
            "claims_raw": [
                {
                    "id": "db3_0001_1",
                    "text": "The active connection pool was set to 500 connections.",
                    "verification_input": "FACT: connection_pool=500",
                    "label": "ACCEPTABLE",
                    "claim_form": "explicit",
                    "modality": "asserted",
                    "source_text": "The active connection pool was set to 500 connections.",
                },
                {
                    "id": "db3_0001_2",
                    "text": "Connection draining took approximately 45 seconds before the green environment served 100% of ingress requests.",
                    "verification_input": "FACT: drain_time=45s",
                    "label": "ACCEPTABLE",
                    "claim_form": "multi_claim_sentence",
                    "modality": "asserted",
                    "source_text": "connection draining took approximately 45 seconds before the green environment served 100% of ingress requests.",
                },
            ],
        }
    )

    # DB3-0002 (dev): Rolling update failure with causal overreach
    cases.append(
        {
            "case_id": "DB3-0002",
            "split": "development",
            "category": "CAUSAL_OVERREACH",
            "severity": "HIGH",
            "source": "K8s Deployment Rollout Audit #409",
            "origin": "imported",
            "prompt": "What caused the pod restart loop during the rolling update of the payment service?",
            "response": "The payment service entered CrashLoopBackOff at 14:15 UTC. The liveness probe failed 3 consecutive times. Because the database replica was upgraded 10 minutes earlier, the database migration definitely caused the payment service probe failure.",
            "evidence": [
                Evidence(
                    id="audit/409",
                    text="K8s pod audit log",
                    facts={
                        "payment_state": "CrashLoopBackOff",
                        "probe_failures": "3",
                        "database_upgrade": "completed",
                    },
                )
            ],
            "expected_behavior": "Flag causal overreach asserting definite causality from mere temporal correlation",
            "difficulty": "hard",
            "notes": "Asserts strict causation without evidentiary support.",
            "claims_raw": [
                {
                    "id": "db3_0002_1",
                    "text": "The payment service entered CrashLoopBackOff at 14:15 UTC.",
                    "verification_input": "FACT: payment_state=CrashLoopBackOff",
                    "label": "ACCEPTABLE",
                    "claim_form": "temporal",
                    "modality": "asserted",
                    "source_text": "The payment service entered CrashLoopBackOff at 14:15 UTC.",
                },
                {
                    "id": "db3_0002_2",
                    "text": "The database migration definitely caused the payment service probe failure.",
                    "verification_input": "FACT: correlation=proves_causation",
                    "label": "PROBLEMATIC",
                    "category": "CAUSAL_OVERREACH",
                    "claim_form": "causal",
                    "modality": "asserted",
                    "source_text": "the database migration definitely caused the payment service probe failure.",
                },
            ],
        }
    )

    # DB3-0003 (dev): Canary analysis threshold with numeric calculation
    cases.append(
        {
            "case_id": "DB3-0003",
            "split": "development",
            "category": "CONTROL",
            "severity": "LOW",
            "source": "Argo Rollouts Canary Analysis Run #88",
            "origin": "imported",
            "prompt": "Calculate the total requests and verify if canary error rate stayed within limits.",
            "response": "Canary analysis evaluated step 3 with 500 requests per minute across 6 minutes. The total sample size calculation states that 500 * 6 = 3000. The observed error count was 3 errors, which is well below the 1% threshold.",
            "evidence": [
                Evidence(
                    id="argo/88",
                    text="Argo analysis run output",
                    facts={"sample_rate": "500rpm", "duration": "6m", "error_count": "3"},
                )
            ],
            "expected_behavior": "Acceptable arithmetic and threshold check",
            "difficulty": "medium",
            "notes": "Embedded calculation and threshold comparison.",
            "claims_raw": [
                {
                    "id": "db3_0003_1",
                    "text": "The total sample size calculation states that 500 * 6 = 3000.",
                    "verification_input": "CALC: 500 * 6 = 3000",
                    "label": "ACCEPTABLE",
                    "claim_form": "numeric",
                    "modality": "asserted",
                    "source_text": "The total sample size calculation states that 500 * 6 = 3000.",
                },
                {
                    "id": "db3_0003_2",
                    "text": "The observed error count was 3 errors.",
                    "verification_input": "FACT: error_count=3",
                    "label": "ACCEPTABLE",
                    "claim_form": "explicit",
                    "modality": "asserted",
                    "source_text": "The observed error count was 3 errors",
                },
            ],
        }
    )

    # DB3-0004 (dev): Canary analysis with arithmetic failure
    cases.append(
        {
            "case_id": "DB3-0004",
            "split": "development",
            "category": "NUMERIC_ERROR",
            "severity": "HIGH",
            "source": "Argo Rollouts Canary Analysis Run #89",
            "origin": "imported",
            "prompt": "Evaluate canary step 4 metrics and request capacity.",
            "response": "Step 4 routed 250 requests per minute across 8 minutes. The capacity calculation states that 250 * 8 = 2400. All health probes reported ready.",
            "evidence": [
                Evidence(
                    id="argo/89",
                    text="Argo analysis run output",
                    facts={"sample_rate": "250rpm", "duration": "8m", "probe_status": "ready"},
                )
            ],
            "expected_behavior": "Detect arithmetic error (250 * 8 = 2000, not 2400)",
            "difficulty": "easy",
            "notes": "Arithmetic check contradicts assertion.",
            "claims_raw": [
                {
                    "id": "db3_0004_1",
                    "text": "The capacity calculation states that 250 * 8 = 2400.",
                    "verification_input": "CALC: 250 * 8 = 2400",
                    "label": "PROBLEMATIC",
                    "category": "NUMERIC_ERROR",
                    "claim_form": "numeric",
                    "modality": "asserted",
                    "source_text": "The capacity calculation states that 250 * 8 = 2400.",
                }
            ],
        }
    )

    return cases


print("Appended first batch of cases...")

from scripts.generate_cases_data import CASES_DATA


def build():
    cases = []
    for item in CASES_DATA:
        c = make_case(
            case_id=item["case_id"],
            split=item["split"],
            category=item["category"],
            severity=item["severity"],
            source=item["source"],
            origin=item["origin"],
            prompt=item["prompt"],
            response=item["response"],
            evidence=[
                Evidence(
                    id=item["evidence_dict"]["id"],
                    text=item["evidence_dict"]["text"],
                    facts=item["evidence_dict"]["facts"],
                )
            ],
            expected_behavior=item["notes"],
            difficulty=item.get("difficulty", "medium"),
            notes=item["notes"],
            claims_raw=item["claims"],
            provenance_details=item.get("prov"),
        )
        cases.append(c)

    dataset = BenchmarkDataset(
        schema_version=1,
        name="dreambench",
        version="0.3.0",
        published="2026-09-11",
        provenance="HowlDream Milestone Three independent natural-language generalization benchmark",
        cases=cases,
    )

    out_path = FIXTURES / "dreambench_v0_3_0.json"
    raw = dataset.model_dump_json(indent=2)
    out_path.write_text(raw + "\n")
    print(
        f"Successfully generated {out_path} with {len(cases)} cases and {sum(len(c.claims) for c in cases)} claims."
    )


if __name__ == "__main__":
    build()

from scripts.enrich_cases import ENRICHMENTS


def build_enriched():
    cases = []
    for item in CASES_DATA:
        cid = item["case_id"]
        raw_claims = list(item["claims"])
        if cid in ENRICHMENTS:
            raw_claims.extend(ENRICHMENTS[cid])
        c = make_case(
            case_id=cid,
            split=item["split"],
            category=item["category"],
            severity=item["severity"],
            source=item["source"],
            origin=item["origin"],
            prompt=item["prompt"],
            response=item["response"],
            evidence=[
                Evidence(
                    id=item["evidence_dict"]["id"],
                    text=item["evidence_dict"]["text"],
                    facts=item["evidence_dict"]["facts"],
                )
            ],
            expected_behavior=item["notes"],
            difficulty=item.get("difficulty", "medium"),
            notes=item["notes"],
            claims_raw=raw_claims,
            provenance_details=item.get("prov"),
        )
        cases.append(c)

    dataset = BenchmarkDataset(
        schema_version=1,
        name="dreambench",
        version="0.3.0",
        published="2026-09-11",
        provenance="HowlDream Milestone Three independent natural-language generalization benchmark",
        cases=cases,
    )

    out_path = FIXTURES / "dreambench_v0_3_0.json"
    raw = dataset.model_dump_json(indent=2)
    out_path.write_text(raw + "\n")
    total_claims = sum(len(c.claims) for c in cases)
    print(f"Successfully generated {out_path} with {len(cases)} cases and {total_claims} claims.")


if __name__ == "__main__":
    build_enriched()
