"""Tests for prior art research and anti-reinvention verification."""

from __future__ import annotations

from typing import ClassVar

from howldream.prior_art import (
    CommandPriorArt,
    LedgerPriorArt,
    MockPriorArt,
    PriorArtMatch,
    concept_query,
    extract_idea_line,
)


def test_extract_idea_line_prefers_idea_prefix():
    text = (
        "PROSE: Some background context\n"
        "IDEA: Compressed zero-copy page cache with bloom filter triage\n"
        "ASSUMPTION: Memory is bounded\n"
        "CALC: 64 * 8 = 512"
    )
    assert (
        extract_idea_line(text)
        == "Compressed zero-copy page cache with bloom filter triage"
    )


def test_extract_idea_line_falls_back_to_first_line():
    text = "A simple standalone proposal without prefix\nNext line"
    assert extract_idea_line(text) == "A simple standalone proposal without prefix"


def test_concept_query_extracts_salient_terms():
    text = "IDEA: Distributed consensus using Byzantine fault tolerant gossip protocols"
    query = concept_query(text)
    assert "consensus" in query
    assert "byzantine" in query or "gossip" in query
    assert "idea" not in query.split()


def test_mock_prior_art_detects_existing_wheel():
    researcher = MockPriorArt()
    redis_match = PriorArtMatch(
        title="Redis In-Memory Key-Value Store",
        source_ref="https://github.com/redis/redis",
        summary="In-memory data structure store used as a database, cache, and message broker.",
        matched_terms=["redis", "cache"],
    )
    researcher.add("redis", redis_match)
    researcher.add("lru cache", redis_match)

    # 1. Idea mentioning existing wheel
    wheel_idea = "IDEA: Build a Redis in-memory key-value cache for session management"
    match = researcher.research(wheel_idea)
    assert match is not None
    assert match.title == "Redis In-Memory Key-Value Store"
    assert match.source_ref == "https://github.com/redis/redis"

    # 2. Idea that is genuinely novel / uncaptured
    novel_idea = "IDEA: Quantum-annealed graph neural routing for satellite mesh networks"
    assert researcher.research(novel_idea) is None


def test_ledger_prior_art_matches_against_prior_entries():
    prior_entries = [
        {
            "id": "tool-bloom-filter",
            "concept": "Probabilistic membership test using bloom filters",
            "source_ref": "rfc-bloom-1970",
        },
        {
            "id": "tool-raft-consensus",
            "concept": "Replicated state machine consensus via Raft leader election",
            "source_ref": "ongaro-raft-2014",
        },
    ]
    researcher = LedgerPriorArt(prior_entries)

    # Matched prior art
    matched = researcher.research("IDEA: Use bloom filters for membership testing in network packets")
    assert matched is not None
    assert matched.title == "tool-bloom-filter"
    assert "bloom" in matched.matched_terms

    # Uncaptured idea
    uncaptured = researcher.research("IDEA: Speculative branch prediction based on thermal dissipation")
    assert uncaptured is None


def test_command_prior_art_executes_template_and_parses_json(tmp_path):
    # Create a small helper script that mimics an external search tool
    helper = tmp_path / "search_helper.py"
    helper.write_text(
        """import sys, json
query = sys.argv[1].lower()
if "postgres" in query or "database" in query:
    print(json.dumps({
        "captured": True,
        "title": "PostgreSQL Object-Relational Database",
        "url": "https://www.postgresql.org",
        "summary": "PostgreSQL is a powerful, open source object-relational database system.",
        "matched_terms": ["database", "postgres"]
    }))
else:
    print(json.dumps({"captured": False}))
"""
    )

    cmd_template = f"python3 {helper} {{query}}"
    researcher = CommandPriorArt(cmd_template)

    # Matches database
    res = researcher.research("IDEA: Implement an ACID compliant relational database")
    assert res is not None
    assert "PostgreSQL" in res.title

    # Novel
    res_novel = researcher.research("IDEA: Holographic storage via optical interference patterns")
    assert res_novel is None


def test_explore_retries_when_prior_art_reinvented_and_finds_novel_idea(tmp_path):
    from howldream.contracts import ExplorationRequest
    from howldream.engine import explore
    from howldream.providers import CAPABILITIES, Response

    # Provider that first outputs a known wheel, but when given reinvention warning,
    # shifts to a novel approach
    class IterativeDreamProvider:
        capabilities: ClassVar[dict[str, bool]] = {**CAPABILITIES, "supports_temperature": True}

        def generate(self, prompt, condition, index, temperature, seed):
            if condition == "baseline":
                return Response("IDEA: Standard in-memory dictionary cache", "ai-model")
            if "Do not reinvent existing wheels" in prompt or "Redis" in prompt:
                # Dream adapted and tried an uncaptured approach!
                return Response(
                    "IDEA: Kernel-bypass compressed page slab with probabilistic eviction\n"
                    "ASSUMPTION: Kernel bypass driver is installed\n"
                    "CALC: 64 * 8 = 512",
                    "ai-model",
                )
            else:
                # First attempt: re-invents Redis!
                return Response(
                    "IDEA: Redis in-memory cache for session store\nASSUMPTION: Memory is cheap",
                    "ai-model",
                )

    researcher = MockPriorArt()
    researcher.add(
        "redis",
        PriorArtMatch(
            title="Redis Key-Value Cache",
            source_ref="https://redis.io",
            summary="Existing open source in-memory data store.",
            matched_terms=["redis", "cache"],
        ),
    )

    req = ExplorationRequest(
        request_id="anti-reinvention-test",
        objective="Design high performance session cache",
        budget={"max_candidates": 1, "max_calls": 5, "max_trials": 1},
    )

    _run_dir, result = explore(
        req, tmp_path / "runs", IterativeDreamProvider(), prior_art_researcher=researcher
    )

    # We expect 2 candidates recorded:
    # 1. The reinvented wheel (status REJECTED / WHEEL_REINVENTED)
    # 2. The novel alternative dreamed upon retry
    assert len(result.candidates) == 2

    reinvented = result.candidates[0]
    assert reinvented.status == "REJECTED"
    assert any("Wheel reinvented" in issue for issue in reinvented.unresolved_issues)
    assert reinvented.provenance.model_extra.get("novelty_status") == "WHEEL_REINVENTED"

    novel = result.candidates[1]
    assert novel.status in ("LOCALLY_VERIFIED", "UNRESOLVED", "CHALLENGED")
    assert "Kernel-bypass" in novel.text
    assert novel.provenance.model_extra.get("novelty_status") == "UNCAPTURED_PRIOR_ART"
    assert novel.provenance.model_extra.get("prior_art_checked") is True


def test_search_prior_art_script_cli():
    import json
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parent.parent / "scripts" / "search_prior_art.py"
    res1 = subprocess.run(
        [sys.executable, str(script), "Redis key-value in-memory cache"],
        capture_output=True,
        text=True,
        check=True,
    )
    out1 = json.loads(res1.stdout)
    assert out1["captured"] is True
    assert "Redis" in out1["title"]

    res2 = subprocess.run(
        [sys.executable, str(script), "Hyper-dimensional holographic ring storage"],
        capture_output=True,
        text=True,
        check=True,
    )
    out2 = json.loads(res2.stdout)
    assert out2["captured"] is False


def test_command_prior_art_with_search_script():
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parent.parent / "scripts" / "search_prior_art.py"
    researcher = CommandPriorArt(f"{sys.executable} {script} {{query}}")
    match = researcher.research("IDEA: Redis in-memory cache engine")
    assert match is not None
    assert "Redis" in match.title

    no_match = researcher.research("IDEA: Novel non-volatile phase change ring memory")
    assert no_match is None


