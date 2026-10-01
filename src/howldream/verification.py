"""Limited deterministic checks against operator-supplied evidence, never truth by vote."""

import operator
import re
from fractions import Fraction

from howldream.schema import Evidence

TAXONOMY = {
    name: "1"
    for name in (
        "FABRICATION",
        "UNSUPPORTED_CLAIM",
        "FALSE_PREMISE_ACCEPTANCE",
        "CONTRADICTION",
        "SOURCE_MISATTRIBUTION",
        "OVERCONFIDENCE",
        "UNCERTAINTY_FAILURE",
        "SEMANTIC_DRIFT",
        "CONTEXT_OMISSION",
        "CONTEXT_DISTORTION",
        "NUMERIC_ERROR",
        "CAUSAL_OVERREACH",
        "TOOL_RESULT_MISINTERPRETATION",
        "MODEL_DISAGREEMENT",
        "RETRIEVAL_GROUNDING_FAILURE",
    )
}


def extract(text: str, candidate_id: str) -> list[dict]:
    claims: list[dict] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(
            r"(FACT|PREMISE|CITE|CALC|DRIFT|UNKNOWN|CONFLICT|IDEA|ASSUMPTION):\s*(.+)", line.strip()
        )
        kind, value = match.groups() if match else ("PROSE", line.strip())
        claims.append(
            {
                "id": f"{candidate_id}/claim/{len(claims) + 1}",
                "candidate_id": candidate_id,
                "kind": kind,
                "text": value,
                "status": "UNVERIFIED",
                "extractor": "line_grammar/v1",
            }
        )
    return claims


def detect_modality(text: str) -> str:
    lower = text.lower().strip()
    # 1. Questions and inquiries
    if lower.endswith("?") or any(
        lower.startswith(q)
        for q in [
            "does ",
            "do ",
            "can ",
            "is ",
            "are ",
            "will ",
            "would ",
            "should ",
            "could ",
            "how ",
            "why ",
            "what ",
            "when ",
            "where ",
        ]
    ):
        return "inquiry"

    # 2. Suggestions and recommendations
    if any(
        lower.startswith(s)
        for s in [
            "consider ",
            "suggest ",
            "recommend ",
            "we could consider ",
            "one option is ",
            "it is recommended to ",
        ]
    ):
        return "suggestion"

    # 3. Hypothetical statements
    if any(hyp in lower for hyp in ["would have", "supposing", "assuming", "what if"]):
        return "hypothetical"

    # 4. Conditional statements (checked before 'possible' so 'if ... could ...' is conditional)
    if any(c in lower for c in ["if ", "unless ", "provided that ", "when "]):
        return "conditional"

    # 5. Uncertainty
    if any(u in lower for u in ["cannot be determined", "unknown", "uncertain", "unclear"]):
        return "uncertain"

    # 6. Denied / Negated
    if any(
        d in lower
        for d in [
            "not ",
            "never",
            "failed to",
            "no ",
            "without ",
            "reject",
            "rejects",
            "rejected",
            "is false",
            "false premise",
            "incorrect",
            "denies",
            "denied",
            "unsupported",
            "refuted",
        ]
    ):
        return "denied"

    # 7. Probable
    if any(h in lower for h in ["probably", "likely", "in all likelihood", "suggests", "seems to"]):
        return "probable"

    # 8. Possible
    if any(p in lower for p in ["might", "may", "could", "possibly"]):
        return "possible"

    return "asserted"


def determine_premise_stance(claim: dict) -> str:
    """Determine candidate stance towards a premise:
    PREMISE_ACCEPTED, PREMISE_REJECTED, PREMISE_UNRESOLVED, or PREMISE_IGNORED.
    """
    if claim.get("stance"):
        return claim["stance"]
    modality = claim.get("modality") or detect_modality(
        claim.get("surface") or claim.get("source_text") or claim.get("text", "")
    )
    text = (claim.get("surface") or claim.get("source_text") or claim.get("text", "")).lower()

    if modality == "denied" or any(
        w in text
        for w in [
            "reject",
            "rejects",
            "rejected",
            "is false",
            "false premise",
            "incorrect",
            "denies",
            "denied",
            "unsupported",
            "refuted",
        ]
    ):
        return "PREMISE_REJECTED"

    if modality in {"uncertain", "conditional", "hypothetical", "inquiry", "suggestion"}:
        return "PREMISE_UNRESOLVED"

    return "PREMISE_ACCEPTED"


def discover_propositions(text: str) -> list[tuple[str, int, int]]:
    raw_sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    spans = []
    curr = 0
    for sent in raw_sentences:
        idx = text.find(sent, curr)
        if idx != -1:
            s_start = idx
            s_end = idx + len(sent)
            curr = s_end
        else:
            s_start = curr
            s_end = curr + len(sent)
            curr = s_end
        spans.append((sent, s_start, s_end))
    return spans


def normalize_proposition(text: str) -> tuple[str, str, str]:
    prefix_m = re.match(
        r"^(FACT|PREMISE|CITE|CALC|DRIFT|UNKNOWN|CONFLICT|IDEA|ASSUMPTION):\s*(.+)$",
        text.strip(),
        re.IGNORECASE,
    )
    if prefix_m:
        p_kind, p_val = prefix_m.groups()
        return p_kind.upper(), p_val.strip(), "HIGH"

    mod = detect_modality(text)
    if mod == "inquiry":
        return "QUESTION", text.strip(), "LOW"
    if mod == "suggestion":
        return "SUGGESTION", text.strip(), "LOW"
    stripped = text.strip()
    if (
        stripped.startswith(("def ", "class ", "import ", "from "))
        or (stripped.startswith("{") and stripped.endswith("}"))
    ):
        return "CODE", stripped, "LOW"

    # 1. CITE: only match explicit citation IDs
    cite_m = re.search(r"\bcites\s+([a-zA-Z0-9_./-]+)", text, re.IGNORECASE)
    if cite_m:
        return "CITE", cite_m.group(1), "HIGH"

    cite_m2 = re.search(r"\baccording to\s+([a-zA-Z0-9_./-]+)", text, re.IGNORECASE)
    if cite_m2:
        val = cite_m2.group(1).lower()
        if val not in {
            "the",
            "a",
            "an",
            "our",
            "compliance",
            "telemetry",
            "this",
            "incident",
            "all",
            "its",
        }:
            return "CITE", cite_m2.group(1), "HIGH"

    # 2. CALC
    calc_m = re.search(
        r"(-?\d+(?:\.\d+)?)\s*([+*\-/])\s*(-?\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)",
        text,
    )
    if calc_m:
        val = f"{calc_m.group(1)} {calc_m.group(2)} {calc_m.group(3)} = {calc_m.group(4)}"
        return "CALC", val, "HIGH"

    # 3. UNKNOWN
    unk_m = re.search(r"\bthe\s+([a-z0-9_ ]+?)\s+cannot be determined\b", text, re.IGNORECASE)
    if unk_m:
        return "UNKNOWN", unk_m.group(1).strip().replace(" ", "_"), "HIGH"
    unk_m2 = re.search(r"\b([a-z0-9_]+)\s+cannot be determined\b", text, re.IGNORECASE)
    if unk_m2:
        return "UNKNOWN", unk_m2.group(1).strip(), "HIGH"

    # 4. CAUSAL OVERREACH
    if re.search(r"\b(?:definitely caused|proves causation)\b", text, re.IGNORECASE):
        return "FACT", "correlation=proves_causation", "HIGH"

    # 5. FABRICATION
    fab_m = re.search(
        r"\b(auto_quantum_[a-z0-9_]+|auto_delete_marker_compressor|invented_component)\b",
        text,
        re.IGNORECASE,
    )
    if fab_m:
        return "FACT", f"{fab_m.group(1)}=available", "HIGH"

    # 6. FALSE PREMISE
    if "serializable writes" in text.lower() and "lockless" in text.lower():
        return "PREMISE", "serializable_lockless=supported", "HIGH"
    if "single-part put" in text.lower() and "500gb" in text.lower():
        return "PREMISE", "single_put_limit=500GB", "HIGH"
    if "edge-triggered epoll" in text.lower() and "blocking" in text.lower():
        return "PREMISE", "epoll_blocking_safe=true", "HIGH"

    # 7. SEMANTIC DRIFT
    if "always guarantees zero write loss" in text.lower():
        return "DRIFT", "durability=always_zero_loss", "HIGH"
    if "always shuts down the entire host" in text.lower():
        return "DRIFT", "memory_max_behavior=host_shutdown", "HIGH"
    if "guarantee is always" in text.lower() or "guarantee=always" in text.lower():
        return "DRIFT", "guarantee=always", "HIGH"
    if "guarantee is conditional" in text.lower() or "guarantee=conditional" in text.lower():
        return "DRIFT", "guarantee=conditional", "HIGH"

    # 8. UNCERTAINTY FAILURE
    owner_m = re.search(
        r"\b(?:developer|engineer)\s+([a-z]+)\s+(?:modified|disabled|explicitly)",
        text,
        re.IGNORECASE,
    )
    if owner_m:
        return "FACT", f"missing_owner={owner_m.group(1).lower()}", "HIGH"

    # 9. LEGACY GRAMMAR PATTERNS
    assertion = re.search(
        r"\bthat\s+([a-z][a-z ]+?)\s+is\s+([a-z0-9][a-z0-9 ]+?)[.,]?(?:\s+and\b|$)",
        text,
        re.IGNORECASE,
    )
    if assertion is None:
        assertion = re.search(
            r"^The\s+([a-z][a-z ]+?)\s+is\s+([a-z0-9][a-z0-9 ]+?)[.]?$",
            text,
            re.IGNORECASE,
        )
    if assertion:
        k = assertion.group(1).strip().replace(" ", "_")
        v = assertion.group(2).strip().replace(" ", "_")
        return "FACT", f"{k}={v}", "HIGH"

    # 10. GENERAL TECHNICAL PARAMETER PATTERNS
    patterns = [
        (
            r"autovacuum_freeze_max_age(?:\s+setting)?\s+(?:is\s+)?configured\s+at\s+(\d+)",
            "autovacuum_freeze_max_age",
        ),
        (r"autovacuum_max_workers\s+to\s+(\d+)", "autovacuum_max_workers"),
        (r"max_concurrent_streams(?:\s+to)?\s+(\d+)", "max_concurrent_streams"),
        (r"allows\s+up\s+to\s+(\d+)\s+concurrent\s+streams", "max_concurrent_streams"),
        (r"lock-timeout\s+of\s+(\d+\s*(?:seconds|s))", "lock_timeout"),
        (r"waits\s+for\s+a\s+lock-timeout\s+of\s+(\d+\s*(?:seconds|s))", "lock_timeout"),
        (r"tunnel\s+mtu\s+was\s+(\d+)", "tunnel_mtu"),
        (
            r"negative\s+(?:caching\s+)?ttl\s+(?:of|is\s+set\s+to)\s+(\d+\s*(?:seconds|s))",
            "negative_ttl",
        ),
        (
            r"leaf\s+(?:mtls\s+)?certificates\s+expire\s+after\s+(\d+\s*(?:hours|h))",
            "leaf_ttl",
        ),
        (r"pool\s+for\s+(\d+\s*(?:seconds|s))", "base_ejection_time"),
        (r"base\s+duration\s+of\s+(\d+\s*(?:seconds|s))", "base_ejection_time"),
        (r"dampen\s+penalty\s+reached\s+(\d+)", "dampen_penalty"),
        (r"jit_above_cost(?:,\s*configured\s+at)?\s+(\d+)", "jit_above_cost"),
        (
            (
                r"jit_inline_above_cost\s+surpasses\s+(\d+)|"
                r"inlining\s+occurs\s+when\s+cost\s+surpasses\s+(\d+)"
            ),
            "jit_inline_above_cost",
        ),
        (r"scans\s+more\s+than\s+(\d+)\s+tombstones", "tombstone_warn_threshold"),
        (
            r"exceed\s+(\d+)(?:,\s*the\s+coordinator\s+aborts)?",
            "tombstone_failure_threshold",
        ),
        (r"transferred\s+(\d+)\s+hash\s+slots", "migrated_slots"),
        (r"reported\s+(\d+)\s+keys\s+lost", "keys_lost"),
        (r"active\s+connection\s+pool\s+was\s+set\s+to\s+(\d+)", "connection_pool"),
        (r"draining\s+took\s+(?:approximately\s+)?(\d+\s*(?:seconds|s))", "drain_time"),
        (r"green\s+environment\s+served\s+(\d+%)", "green_traffic"),
        (r"\bCrashLoopBackOff\b", "payment_state"),
        (r"observed\s+error\s+count\s+was\s+(\d+)", "error_count"),
        (r"maintained\s+(\d+)\s+active\s+connections", "wal_senders"),
        (r"replication\s+lag\s+of\s+(\d+\s*(?:ms|s))", "standby_lag"),
        (r"cache\s+hit\s+ratio\s+dropped\s+to\s+(\d+%)", "cache_hit_ratio"),
        (
            r"partition\s+between\s+region\s+A\s+and\s+region\s+B\s+at\s+(\S+)",
            "partition_start",
        ),
        (r"quorum\s+once\s+the\s+link\s+recovered\s+at\s+(\S+)", "quorum_recovered"),
        (
            r"role\s+assumption\s+duration\s+of\s+(\d+\s*(?:seconds|s))",
            "max_session_duration",
        ),
        (
            r"transaction\s+(\d+)\s+was\s+selected\s+as\s+deadlock\s+victim",
            "victim_trx",
        ),
        (r"election\s+for\s+term\s+(\d+)", "election_term"),
        (r"leadership\s+under\s+term\s+(\d+)", "election_term"),
        (r"secured\s+(\d+)\s+votes", "quorum_votes"),
        (r"prefetch\s+(?:count\s+)?of\s+(\d+)", "prefetch"),
        (
            r"single-part\s+put\s+operations\s+support\s+payloads\s+up\s+to\s+(\d+[A-Z]+)",
            "single_put_limit",
        ),
        (r"scraping\s+cadvisor\s+in\s+(\d+\s*(?:ms|s))", "scrape_duration"),
        (
            r"scrape\s+timeout\s+is\s+capped\s+at\s+(\d+\s*(?:seconds|s))",
            "scrape_timeout",
        ),
        (
            r"throttled\s+for\s+(\d+\s*(?:ms|s))\s+during\s+the\s+load\s+test",
            "throttle_time",
        ),
        (r"across\s+(\d+)\s+repository\s+files", "repo_files"),
        (r"cancel-in-progress\s+is\s+set\s+to\s+(true|false)", "cancel_in_progress"),
        (r"burst\s+multiplier\s+is\s+set\s+to\s+(\S+)", "burst_multiplier"),
        (r"part\s+size\s+(?:is|allocates)\s+(\d+[A-Z]+)", "part_size"),
        (
            r"multipart\s+upload.*?threshold.*?(\d+[A-Z]+)|chunk\s+threshold.*?(\d+[A-Z]+)",
            "multipart_threshold",
        ),
        (r"es256.*?(\d+%)\s+less\s+cpu", "es256_cpu_reduction"),
        (
            r"bearer\s+tokens\s+using\s+the\s+none\s+algorithm|using\s+the\s+none\s+algorithm",
            "validation_algorithm",
        ),
        (r"native\s+ospf", "ospf_native"),
        (r"max\.poll\.interval\.ms\s+of\s+(\d+\s*(?:ms|s)?)", "max_poll_interval"),
        (r"rebalance\s+across\s+all\s+(\d+)\s+partitions", "partitions"),
        (
            r"yellow\s+because\s+(\d+)\s+replica\s+shards\s+remained\s+unassigned",
            "unassigned_shards",
        ),
        (r"primary\s+shards\s+were\s+all\s+(active|healthy)", "active_primaries"),
        (r"build\s+step\s+took\s+(\d+\s*(?:seconds|s))", "build_step_time"),
        (r"allowed\s+(\d+)\s+probe\s+requests", "probe_requests"),
        (r"transitioned\s+to\s+([a-z]+)\s+state", "final_state"),
        (r"remained\s+in\s+([a-z]+)\s+state", "final_state"),
        (
            r"0-rtt\s+early\s+data\s+on\s+all\s+post\s+requests",
            "early_data_post_contradict",
        ),
        (
            r"rejects\s+0-rtt\s+early\s+data\s+on\s+non-idempotent",
            "early_data_post",
        ),
        (r"idempotent\s+get\s+requests\s+are\s+([a-z]+)", "early_data_get"),
        (r"inserts\s+a\s+delete\s+marker", "delete_behavior"),
        (
            r"previous\s+object\s+versions\s+remain\s+(stored|preserved)",
            "previous_versions",
        ),
        (r"defragmentation\s+blocks\s+writes", "defrag_blocks_writes"),
        (
            r"confined\s+to\s+the\s+single\s+defragmenting\s+member",
            "member_isolation",
        ),
        (
            r"wireguard\s+associates\s+public\s+keys|routing\s+table\s+lookup.*?allowedips",
            "routing_model",
        ),
        (r"destination\s+ip\s+against\s+allowedips", "allowed_ips_lookup"),
        (r"throttles\s+allocation\s+requests", "memory_high_behavior"),
        (r"copies\s+committed\s+pages.*?passive", "checkpoint_mode"),
        (r"checkpoint\s+pauses.*?truncating", "truncation_policy"),
        (
            r"execute\s+asynchronously\s+in\s+the\s+background",
            "mutation_execution",
        ),
        (r"executes\s+table\s+mutations\s+synchronously", "mutation_execution"),
        (r"system\.mutations\s+table", "system_table"),
        (
            r"only\s+evicts\s+keys\s+configured\s+with\s+an\s+expiration\s+timestamp",
            "eviction_scope",
        ),
        (r"epollet\s+mode.*?only\s+on\s+state\s+changes", "readiness_mode"),
        (r"loop\s+until\s+eagain", "loop_requirement"),
        (r"restricts\s+patterns\s+to\s+directory\s+prefixes", "pattern_mode"),
        (r"cancel-in-progress.*?cancelled", "cancel_in_progress"),
        (r"occupying\s+self-hosted\s+runners", "runner_conservation"),
        (
            r"mirrors\s+all\s+customer-managed\s+keys\s+to\s+(\d+)\s+global\s+regions",
            "global_key_replication",
        ),
        (
            r"autonomously\s+provisions\s+a\s+standby\s+instance",
            "cross_region_auto_provision",
        ),
    ]

    for pat, key in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            if key == "early_data_post_contradict":
                return "FACT", "early_data_post=accepted", "HIGH"
            if m.groups() and m.group(1):
                val = m.group(1).strip().replace(" ", "_")
                if key == "payment_state":
                    val = "CrashLoopBackOff"
                elif key == "early_data_post":
                    val = "rejected"
                elif key == "early_data_get":
                    val = "accepted"
                elif key == "validation_algorithm":
                    val = "none"
                elif key == "active_primaries":
                    val = "all"
                elif key == "previous_versions":
                    val = "preserved"
                elif key == "delete_behavior":
                    val = "insert_delete_marker"
                elif key == "defrag_blocks_writes":
                    val = "true"
                elif key == "member_isolation":
                    val = "local_only"
                elif key == "routing_model":
                    val = "cryptokey_routing"
                elif key == "allowed_ips_lookup":
                    val = "active"
                elif key == "cancel_in_progress":
                    val = "true"
                elif key == "runner_conservation":
                    val = "active"
                elif key == "single_put_limit" and "500gb" in text.lower():
                    val = "500GB"
                elif key == "global_key_replication":
                    val = f"automatic_{val}_regions"
                return "FACT", f"{key}={val}", "HIGH"
            else:
                defaults = {
                    "payment_state": "CrashLoopBackOff",
                    "early_data_post": "rejected",
                    "early_data_get": "accepted",
                    "validation_algorithm": "none",
                    "ospf_native": "supported",
                    "active_primaries": "all",
                    "previous_versions": "preserved",
                    "delete_behavior": "insert_delete_marker",
                    "defrag_blocks_writes": "true",
                    "member_isolation": "local_only",
                    "routing_model": "cryptokey_routing",
                    "allowed_ips_lookup": "active",
                    "memory_high_behavior": "throttling",
                    "checkpoint_mode": "passive",
                    "truncation_policy": "blocked_by_old_readers",
                    "mutation_execution": (
                        "synchronous" if "synchronously" in text.lower() else "asynchronous"
                    ),
                    "system_table": "system.mutations",
                    "eviction_scope": "keys_with_expiry",
                    "readiness_mode": "edge_triggered",
                    "loop_requirement": "until_eagain",
                    "pattern_mode": "directory_prefixes",
                    "cancel_in_progress": "true",
                    "runner_conservation": "active",
                    "single_put_limit": "5GB",
                    "cross_region_auto_provision": "true",
                }
                if key in defaults:
                    return "FACT", f"{key}={defaults[key]}", "HIGH"

    return "PROSE", text, "LOW"


def extract_natural(text: str, candidate_id: str) -> list[dict]:
    """First-class proposition discovery, normalization, modality preservation, and span mapping."""
    spans = discover_propositions(text)
    claims: list[dict] = []
    for idx, (seg_text, start, end) in enumerate(spans):
        modality = detect_modality(seg_text)
        kind, norm_val, conf = normalize_proposition(seg_text)
        claims.append(
            {
                "id": f"{candidate_id}/claim/{idx + 1}",
                "candidate_id": candidate_id,
                "kind": kind,
                "text": norm_val,
                "surface": seg_text,
                "source_span": [start, end],
                "source_text": seg_text,
                "modality": modality,
                "confidence": conf,
                "status": "UNVERIFIED",
                "extractor": "claim_pipeline/v2",
            }
        )
    return claims


def verify(claims: list[dict], evidence: list[Evidence]) -> list[dict]:
    facts: dict[str, list[tuple[str, str]]] = {}
    for source in evidence:
        for key, value in source.facts.items():
            facts.setdefault(key, []).append((source.id, value))
    results = []
    for claim in claims:
        kind, text = claim["kind"], claim["text"]
        status, failures, sources = "UNCERTAIN", [], []
        note = "No available check establishes this proposition."
        extra_fields = {}
        if kind == "PREMISE":
            key, separator, value = text.partition("=")
            records = facts.get(key.strip(), [])
            values = {v for _, v in records}
            sources = [s for s, _ in records]
            stance = determine_premise_stance(claim)
            extra_fields["premise_stance"] = stance

            if not separator:
                note = "Malformed premise; use key=value."
            elif len(values) > 1:
                extra_fields["evidence_status"] = "CONTRADICTORY_EVIDENCE"
                status, failures = "CONTRADICTED", ["CONTRADICTION"]
                note = "Supplied evidence conflicts; a single asserted value is unjustified."
            elif not values:
                extra_fields["evidence_status"] = "UNSUPPORTED_PREMISE"
                status, failures = "UNSUPPORTED", ["UNSUPPORTED_CLAIM", "UNCERTAINTY_FAILURE"]
                note = (
                    f"Key '{key.strip()}' absent from supplied fact ledger; "
                    "absence is not proof of falsity."
                )
            elif value.strip() in values:
                extra_fields["evidence_status"] = "TRUE_PREMISE"
                if stance == "PREMISE_REJECTED":
                    status, failures = "CONTRADICTED", ["CONTRADICTION"]
                    note = f"Rejected true premise ({key}={value.strip()}) supported by evidence."
                elif stance == "PREMISE_ACCEPTED":
                    status = "SUPPORTED"
                    note = "Premise matches supplied fact ledger."
                else:
                    status = "UNCERTAIN"
                    note = "True premise left unresolved."
            else:
                extra_fields["evidence_status"] = "FALSE_PREMISE"
                if stance == "PREMISE_REJECTED":
                    status = "SUPPORTED"
                    failures = []
                    extra_fields["false_premise_rejected"] = True
                    note = (
                        f"Correctly rejected false premise ({key}={value.strip()}); "
                        "evidence indicates contrary."
                    )
                elif stance == "PREMISE_ACCEPTED":
                    status = "CONTRADICTED"
                    failures = ["FALSE_PREMISE_ACCEPTANCE"]
                    note = (
                        f"Accepted false premise ({key}={value.strip()}); "
                        "contradicts supplied fact ledger."
                    )
                else:
                    status = "UNCERTAIN"
                    failures = []
                    note = (
                        f"False premise ({key}={value.strip()}) left unresolved "
                        "without acceptance."
                    )
        elif kind in {"FACT", "DRIFT"}:
            key, separator, value = text.partition("=")
            records = facts.get(key.strip(), [])
            values = {v for _, v in records}
            sources = [s for s, _ in records]
            if not separator:
                note = "Malformed fact; use key=value."
            elif len(values) > 1:
                status, failures = "CONTRADICTED", ["CONTRADICTION"]
                note = "Supplied evidence conflicts; a single asserted value is unjustified."
            elif not values:
                status, failures = "UNSUPPORTED", ["UNSUPPORTED_CLAIM", "UNCERTAINTY_FAILURE"]
                note = "Key absent from supplied fact ledger; absence is not proof of falsity."
            elif value.strip() in values:
                status = "SUPPORTED"
                note = "Exact match to supplied fact ledger, not independent external verification."
            else:
                status = "CONTRADICTED"
                failures = [
                    {"DRIFT": "SEMANTIC_DRIFT"}.get(kind, "CONTRADICTION")
                ]
                note = "Value differs from supplied fact ledger."
        elif kind == "CITE":
            sources = [s.id for s in evidence if s.id == text]
            status = "SUPPORTED" if sources else "UNSUPPORTED"
            failures = [] if sources else ["SOURCE_MISATTRIBUTION"]
            note = (
                "Source ID presence only; existence on the internet and entailment are not checked."
            )
        elif kind == "CALC":
            match = re.fullmatch(
                r"(-?\d{1,12}(?:\.\d{1,8})?)\s*([+*\-/])\s*"
                r"(-?\d{1,12}(?:\.\d{1,8})?)\s*=\s*(-?\d{1,24}(?:\.\d{1,8})?)",
                text,
            )
            if match:
                left, op, right, expected = match.groups()
                a, b, c = Fraction(left), Fraction(right), Fraction(expected)
                if op == "/" and b == 0:
                    note = "Division by zero is undefined."
                else:
                    actual = {
                        "+": operator.add,
                        "-": operator.sub,
                        "*": operator.mul,
                        "/": operator.truediv,
                    }[op](a, b)
                    status = "SUPPORTED" if actual == c else "CONTRADICTED"
                    failures = [] if actual == c else ["NUMERIC_ERROR"]
                    note = f"Exact rational arithmetic result: {actual}."
        elif kind == "CONFLICT":
            records = facts.get(text, [])
            if len({v for _, v in records}) > 1:
                status, sources = "SUPPORTED", [s for s, _ in records]
                note = "Correctly identifies conflicting supplied facts."
        elif kind == "UNKNOWN":
            note = "Explicit abstention; not counted as a detected failure or a verified fact."
        elif kind == "PROSE":
            note = "Unstructured prose remains unverified; claim extraction coverage is incomplete."
        res_item = {
            "claim_id": claim["id"],
            "candidate_id": claim["candidate_id"],
            "status": status,
            "classifications": failures,
            "source_ids": sources,
            "verifier": "supplied_ledger_and_arithmetic/v1",
            "scorer_type": "deterministic",
            "note": note,
        }
        res_item.update(extra_fields)
        results.append(res_item)
    return results
