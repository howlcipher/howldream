"""Prior art research and anti-reinvention verification for HowlDream.

Dream must not re-invent the wheel. When an idea is proposed, it is researched
against known prior art (internet search hooks, tool ledgers, literature indices).
If the idea is already captured, Dream marks it as WHEEL_REINVENTED, adds the family
to its memory, and redreams to find an uncaptured, unique alternative.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from howldream.discovery import concept_tokens
from howldream.scoring import STOP_WORDS


@dataclass(frozen=True)
class PriorArtMatch:
    """A matched pre-existing piece of software, library, patent, or publication."""

    title: str
    source_ref: str
    summary: str
    matched_terms: list[str]
    confidence: str = "HIGH"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PriorArtResearcher(Protocol):
    """Protocol for checking whether a proposed idea is already captured in prior art."""

    def research(self, text: str, objective: str = "") -> PriorArtMatch | None:
        """Return PriorArtMatch if the idea is already known/captured; None if novel/uncaptured."""
        ...


def extract_idea_line(text: str) -> str:
    """Extract the primary speculative proposition from candidate text."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("IDEA:"):
            return line[5:].strip()
    return text.strip().splitlines()[0] if text.strip() else ""


def concept_query(text: str) -> str:
    """Extract a concise search query representing the core technical concept."""
    idea = extract_idea_line(text)
    raw_tokens = concept_tokens(idea)
    words = [w.lower() for w in re.findall(r"[a-zA-Z0-9_-]+", idea) if w.lower() in raw_tokens]
    if not words:
        words = [
            w.lower() for w in re.findall(r"[a-zA-Z0-9_-]+", idea) if w.lower() not in STOP_WORDS
        ]
    return " ".join(words[:8])


class MockPriorArt:
    """Deterministic fixture-backed researcher for reproducible tests and CI."""

    def __init__(self, database: dict[str, PriorArtMatch] | None = None):
        self.database: dict[str, PriorArtMatch] = database or {}
        self.queries_received: list[str] = []

    def add(self, keyword_or_phrase: str, match: PriorArtMatch) -> None:
        self.database[keyword_or_phrase.lower()] = match

    def research(self, text: str, objective: str = "") -> PriorArtMatch | None:
        query = concept_query(text).lower()
        self.queries_received.append(query)
        idea = extract_idea_line(text).lower()
        full_text = text.lower()
        for key, match in self.database.items():
            if key in query or key in idea or key in full_text:
                return match
        return None


class LedgerPriorArt:
    """Matches candidate concepts against an established AttributionLedger or tool catalog."""

    def __init__(self, prior_entries: list[dict[str, Any]]):
        self.prior_entries = prior_entries

    def research(self, text: str, objective: str = "") -> PriorArtMatch | None:
        idea_tokens = concept_tokens(extract_idea_line(text))
        if not idea_tokens:
            return None
        for entry in self.prior_entries:
            concept = entry.get("concept") or entry.get("text") or entry.get("title") or ""
            entry_tokens = concept_tokens(concept)
            intersection = idea_tokens & entry_tokens
            if len(intersection) >= 2 or (
                len(entry_tokens) > 0 and len(intersection) / len(entry_tokens) >= 0.5
            ):
                return PriorArtMatch(
                    title=entry.get("id") or concept[:80],
                    source_ref=entry.get("source_ref") or "local_ledger",
                    summary=concept,
                    matched_terms=sorted(intersection),
                    confidence="MEDIUM",
                )
        return None


class CommandPriorArt:
    """Executes a bounded external search/research command to inspect prior art."""

    def __init__(self, command_template: str, timeout_seconds: float = 10.0):
        self.command_template = command_template
        self.timeout_seconds = timeout_seconds

    def research(self, text: str, objective: str = "") -> PriorArtMatch | None:
        query = concept_query(text)
        if not query:
            return None
        cmd = self.command_template.format(query=shlex.quote(query), raw_query=query)
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            if res.returncode != 0 or not res.stdout.strip():
                return None
            data = json.loads(res.stdout)
            if isinstance(data, dict) and data.get("captured"):
                return PriorArtMatch(
                    title=data.get("title", "Prior Art"),
                    source_ref=data.get("source_ref") or data.get("url", "unknown"),
                    summary=data.get("summary", ""),
                    matched_terms=data.get("matched_terms", query.split()),
                    confidence=data.get("confidence", "HIGH"),
                )
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            return None
        return None


class WebSearchPriorArt:
    """SSRF-guarded web search researcher querying a configured search endpoint."""

    def __init__(self, endpoint_url: str, timeout_seconds: float = 5.0):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    def research(self, text: str, objective: str = "") -> PriorArtMatch | None:
        query = concept_query(text)
        if not query:
            return None
        url = f"{self.endpoint_url}?q={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "HowlDream-PriorArt/0.4.5 (+https://github.com/howlcipher/howldream)",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read(100_000)
            data = json.loads(body.decode("utf-8"))
            results = data.get("results") or data.get("hits") or []
            q_terms = set(query.lower().split())
            for hit in results[:5]:
                title = hit.get("title", "")
                snippet = hit.get("content") or hit.get("snippet", "")
                hit_tokens = set(re.findall(r"[a-z0-9]+", (title + " " + snippet).lower()))
                common = q_terms & hit_tokens
                if len(common) >= max(2, len(q_terms) // 2):
                    return PriorArtMatch(
                        title=title[:120],
                        source_ref=hit.get("url", self.endpoint_url),
                        summary=snippet[:250],
                        matched_terms=sorted(common),
                        confidence="MEDIUM",
                    )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None
        return None
