#!/usr/bin/env python3
"""Prior Art Search CLI Helper for HowlDream.

Used with `howldream explore --prior-art-command "python scripts/search_prior_art.py {query}"`
or as an independent tool to verify whether an engineering concept or candidate
duplicates existing prior art, known architectures, or published open-source tools.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BUILTIN_PRIOR_ART: list[dict[str, Any]] = [
    {
        "title": "Apache Kafka Event Streaming Platform",
        "keywords": ["kafka", "commit log", "partitioned topic", "consumer group"],
        "source_ref": "https://kafka.apache.org",
        "summary": "Distributed event streaming platform using partitioned append-only commit logs.",
        "confidence": "HIGH",
    },
    {
        "title": "Redis In-Memory Data Store",
        "keywords": ["redis", "in-memory key-value", "in-memory cache", "remote dictionary"],
        "source_ref": "https://redis.io",
        "summary": "In-memory database and cache with optional disk persistence and pub/sub.",
        "confidence": "HIGH",
    },
    {
        "title": "RabbitMQ Message Broker",
        "keywords": ["rabbitmq", "amqp", "message exchange", "dead letter exchange"],
        "source_ref": "https://www.rabbitmq.com",
        "summary": "Distributed message broker implementing AMQP with flexible exchange routing.",
        "confidence": "HIGH",
    },
    {
        "title": "Memcached Distributed Cache",
        "keywords": ["memcached", "slab allocator", "distributed memory object cache"],
        "source_ref": "https://memcached.org",
        "summary": "High-performance, distributed memory object caching system.",
        "confidence": "HIGH",
    },
    {
        "title": "SQLite Embedded Database",
        "keywords": ["sqlite", "serverless database", "embedded b-tree database"],
        "source_ref": "https://sqlite.org",
        "summary": "C-language library implementing a small, fast, self-contained SQL database.",
        "confidence": "HIGH",
    },
]


def normalize_tokens(text: str) -> set[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", " ", text.lower())
    return {w for w in cleaned.split() if len(w) > 2}


def check_prior_art(
    query: str,
    index_path: Path | None = None,
    mock_match: str | None = None,
    use_builtin: bool = True,
) -> dict[str, Any]:
    norm_query = query.lower()
    query_tokens = normalize_tokens(query)

    # 1. Explicit mock match flag (for deterministic testing & dogfood scripts)
    if mock_match and mock_match.lower() in norm_query:
        return {
            "captured": True,
            "matched": True,
            "title": f"Captured Prior Art: {mock_match}",
            "source_ref": f"catalog://prior-art/{mock_match.lower().replace(' ', '-')}",
            "summary": f"Known engineering design matching '{mock_match}'.",
            "matched_terms": [mock_match.lower()],
            "confidence": "HIGH",
        }

    catalog: list[dict[str, Any]] = []

    # 2. External JSON catalog index if provided
    if index_path and index_path.exists():
        try:
            with open(index_path, encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    catalog.extend(loaded)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: failed to load catalog {index_path}: {e}", file=sys.stderr)

    # 3. Built-in industry catalog
    if use_builtin:
        catalog.extend(BUILTIN_PRIOR_ART)

    # 4. Search catalog entries
    for entry in catalog:
        keywords = entry.get("keywords", [])
        entry_title = entry.get("title", "")

        matched_terms: list[str] = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in norm_query or (" " not in kw_lower and kw_lower in query_tokens):
                matched_terms.append(kw)

        if not matched_terms and entry_title.lower() in norm_query:
            matched_terms.append(entry_title)

        if matched_terms:
            return {
                "captured": True,
                "matched": True,
                "title": entry.get("title", "Existing Tool"),
                "source_ref": entry.get("source_ref", entry.get("url", "catalog://known-art")),
                "summary": entry.get("summary", "Documented prior engineering design."),
                "matched_terms": matched_terms,
                "confidence": entry.get("confidence", "HIGH"),
            }

    return {"captured": False, "matched": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Search prior art for HowlDream")
    parser.add_argument("query", nargs="?", default="", help="Query or candidate proposition")
    parser.add_argument(
        "--index", type=Path, default=None, help="Path to JSON catalog of prior art"
    )
    parser.add_argument("--mock-match", help="Trigger deterministic match if substring present")
    parser.add_argument(
        "--no-builtin", action="store_true", help="Disable built-in standard catalog"
    )

    args = parser.parse_args()
    result = check_prior_art(
        query=args.query,
        index_path=args.index,
        mock_match=args.mock_match,
        use_builtin=not args.no_builtin,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
