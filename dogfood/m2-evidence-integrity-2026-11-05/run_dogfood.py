"""M2 dogfood: drive the real howldream and howlproof CLIs over a fixed v4 corpus.

Nothing here edits an archive. Inputs are copies under inputs/. Every command, exit code and
output is written under logs/ and results/. The only network use is one explicit, bounded
`howlproof acquire --url` (recorded either way).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

W = Path("/run/media/howlcipher/tallgeese/dev/ruby_ideas/m2_dogfood")
PROOF = "/run/media/howlcipher/tallgeese/dev/howlproof/.venv/bin/python"
DREAM = "/run/media/howlcipher/tallgeese/dev/howldream/.venv/bin/python"
OLD_SRC = W / "old_proof_src" / "src"
RAW = W / "inputs" / "claude_raw"
LOGS = W / "logs"
LOG: list[dict] = []


def run(label: str, argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    LOG.append({"label": label, "argv": argv, "exit": done.returncode})
    (LOGS / f"{label}.stdout").write_text(done.stdout)
    (LOGS / f"{label}.stderr").write_text(done.stderr)
    return done


def proof(label: str, *args: str, timeout: int = 120):
    return run(label, [PROOF, "-m", "howlproof.cli", *args], timeout)


def old_proof(label: str, *args: str):
    code = (
        f"import sys; sys.path.insert(0, {str(OLD_SRC)!r}); "
        "from howlproof.cli import main; sys.exit(main(sys.argv[1:]))"
    )
    return run(label, [PROOF, "-I", "-c", code, *args])


def dream(label: str, *args: str):
    return run(label, [DREAM, "-m", "howldream.cli", *args])


def statuses(result_stdout: str) -> dict[str, dict]:
    doc = json.loads(result_stdout)
    out = {}
    for check in doc["checks"]:
        detail = check.get("detail") or {}
        if "claim_status" in detail:
            out[detail["claim_id"]] = {
                "claim_status": detail["claim_status"],
                "check_outcome": detail.get("check_outcome"),
                "proof_check_status": check["status"],
                "explanation": detail["explanation"],
                "assurance": detail.get("assurance"),
                "scope_limited": detail.get("scope_limited"),
                "conflicts": detail.get("conflicts"),
                "also_found_in": detail.get("also_found_in"),
            }
    return out


def acquire_all(store: Path) -> dict[str, dict]:
    sources = {
        "mutant_readme": ("mutant_README.md", "https://github.com/mbj/mutant"),
        "mutant_skill": ("mutant_SKILL.md", "https://github.com/mbj/mutant"),
        "rubylang_news": ("rubylang_news.html", "https://www.ruby-lang.org/en/news/"),
        "ruby400_notes": (
            "ruby400_notes.html",
            "https://www.ruby-lang.org/en/news/2025/12/25/ruby-4-0-0-released/",
        ),
        "rv_readme": ("rv_README.md", "https://github.com/spinel-coop/rv"),
        "mame_readme": ("mame_README.md", "https://github.com/mame/ai-coding-lang-bench"),
    }
    records = {}
    for name, (filename, url) in sources.items():
        done = proof(
            f"acquire_{name}", "acquire", "--store", str(store), "--file", str(RAW / filename),
            "--source-url", url, "--operator", "claude-m2-dogfood",
        )  # fmt: skip
        assert done.returncode == 0, done.stderr
        records[name] = json.loads(done.stdout)
    return records


def pointer(rec: dict) -> dict:
    return {"id": rec["id"], "content_sha256": rec["content_sha256"]}


def ext(ref: str, by: str) -> dict:
    return {
        "source_type": "EXTERNAL_OBSERVATION",
        "produced_by": by,
        "source_ref": ref,
        "independent_of_implementation": True,
        "represents_observed_reality": True,
    }


def build_claude_corpus(records: dict, live: dict | None) -> tuple[dict, list[dict]]:
    def fc(fact, op, expected, tol="0", nature=None):
        check = {"type": "fact_compare", "fact": fact, "op": op, "expected": expected,
                 "tolerance": tol}  # fmt: skip
        if nature:
            check["nature"] = nature
        return check

    def claim(cid, text, category, refs, check=None, **extra):
        return {"id": cid, "candidate_id": "m2/claude-corpus", "kind": "FACT", "text": text,
                "status": "UNVERIFIED", "category": category, "evidence_refs": refs,
                "check": check, **extra}  # fmt: skip

    news_refs = ["rubylang_news"] + (["rubylang_news_live"] if live else [])
    claims = [
        # (3) Claude's Mutant discrepancy, wording and check exactly as authored in v4
        claim("k02-3", "The Mutant README documents an AI-agent integration.", "EMPIRICAL",
              ["mutant_readme"], fc("agent_integration_documented", "eq", "1"),
              subject_terms=["Mutant"]),
        # same wording; the narrow, scoped check that v4 lacked
        claim("k02-3-scoped", "The Mutant README documents an AI-agent integration.", "EMPIRICAL",
              ["mutant_readme"], {"type": "text_presence", "term": "agent", "expect": "present"},
              subject_terms=["Mutant"],
              checked_proposition="The text of the Mutant README contains the word 'agent'",
              scope={"artifact": "mbj/mutant README.md", "extent": "SINGLE_FILE"}),
        claim("k02-5", "The mutant repository ships an agent skill file (SKILL.md).", "EMPIRICAL",
              ["mutant_skill"], fc("skill_file_http_status", "eq", "200")),
        # (4) one real Ruby release fact (the check is on the page's text, not on the world)
        claim("rel-4-0-9", "Ruby 4.0.9 has been released.", "EMPIRICAL", news_refs,
              {"type": "text_presence", "term": "Ruby 4.0.9 Released", "expect": "present"},
              subject_terms=["Ruby"],
              checked_proposition="The ruby-lang.org news page lists 'Ruby 4.0.9 Released'",
              scope={"artifact": "ruby-lang.org/en/news/", "extent": "SINGLE_PAGE"}),
        # (5) a reproducible arithmetic claim, as authored in v4 (k03-3)
        claim("k03-3", "Arithmetic: (0.62-0.36)/0.62 = 0.419 (Ruby cost 41.9% below TypeScript, "
              "same benchmark).", "TECHNICAL", ["mame_readme"],
              {"type": "arithmetic", "expression": "(0.62 - 0.36) / 0.62", "op": "approx",
               "expected": "0.419", "tolerance": "0.001"}),
        # (6) an unverified adoption prediction, as authored in v4 (k06-3)
        claim("k06-3", "Ruby will return to the TIOBE top 10 by 2028.", "VALUE_JUDGMENT", []),
        # (7) an outdated fact against a newer authoritative page (constructed from archived facts)
        claim("ruby-4-0-0-latest", "Ruby 4.0.0 is the most recent Ruby 4.0 release.", "EMPIRICAL",
              ["ruby400_notes", "rubylang_news"],
              {"type": "text_presence", "term": "Ruby 4.0.9 Released", "expect": "absent"},
              subject_terms=["Ruby"],
              checked_proposition="Neither cited ruby-lang.org page lists 'Ruby 4.0.9 Released'",
              scope={"artifact": "two ruby-lang.org pages", "extent": "TWO_PAGES"}),
        # (8) a genuine document that does not address the claim (it contains the number)
        claim("rubydex-index-time", "Rubydex indexes a project in under 2 seconds.", "EMPIRICAL",
              ["rv_readme"], fc("index_seconds", "le", "2 seconds", nature="reported_fact"),
              subject_terms=["Rubydex"]),
    ]
    cand = {
        "candidate_id": "m2/claude-corpus", "source_run_id": "m2-dogfood-1",
        "parent_request_id": "m2-dogfood-1", "objective": "M2 evidence integrity dogfood",
        "text": "Fixed v4 claim corpus for the M2 evidence trust model.", "claims": claims,
        "assumptions": [],
        "provenance": {"producer_component": "howldream", "observation_kind": "EXTERNALLY_OBSERVED",
                       "origin": {"component": "claude-m2-dogfood", "provider": None, "model": None},
                       "created_at": "2026-11-05T00:00:00+00:00"},
    }  # fmt: skip

    def evidence(eid, facts, rec, ref, by, published=None):
        facts = dict(facts)
        if published:
            facts["published_at"] = published
        return {"id": eid, "text": "", "facts": facts, "provenance": ext(ref, by),
                "acquisition": pointer(rec)}  # fmt: skip

    ev = [
        evidence("mutant_readme", {"agent_integration_documented": "0"},
                 records["mutant_readme"], "https://github.com/mbj/mutant", "mbj/mutant"),
        evidence("mutant_skill", {"skill_file_http_status": "200"},
                 records["mutant_skill"], "https://github.com/mbj/mutant", "mbj/mutant"),
        evidence("rubylang_news", {}, records["rubylang_news"],
                 "https://www.ruby-lang.org/en/news/", "ruby-lang.org", "2026-10-23T00:00:00Z"),
        evidence("ruby400_notes", {}, records["ruby400_notes"],
                 "https://www.ruby-lang.org/en/news/2025/12/25/ruby-4-0-0-released/",
                 "ruby-lang.org", "2025-12-25T00:00:00Z"),
        evidence("rv_readme", {"index_seconds": "1.8 seconds"}, records["rv_readme"],
                 "https://github.com/spinel-coop/rv", "spinel-coop/rv"),
        evidence("mame_readme", {}, records["mame_readme"],
                 "https://github.com/mame/ai-coding-lang-bench", "mame"),
    ]  # fmt: skip
    if live:
        ev.append(evidence("rubylang_news_live", {}, live, live["requested_url"], "ruby-lang.org",
                           live["retrieved_at"]))
    return cand, ev


def main() -> None:
    for sub in ("results", "bundles", "assessments", "store", "live_store", "proof_out"):
        shutil.rmtree(W / sub, ignore_errors=True)
        (W / sub).mkdir()
    LOGS.mkdir(exist_ok=True)
    summary: dict = {"agy": {}, "claude": {}}

    # --- AGY frozen bundles: new Proof (no acquisition ever happened) versus old Proof ---------
    for cand in ("cand-01-rubydex-mcp", "cand-03-rubypack"):
        src = W / "inputs" / "agy_bundles" / cand
        old = old_proof(f"agy_{cand}_old", "evaluate", str(src), "--profile", "research",
                        "--evidence-root", str(W / "proof_out" / "old"), "--json")  # fmt: skip
        new = proof(f"agy_{cand}_new", "evaluate", str(src), "--profile", "research",
                    "--evidence-root", str(W / "proof_out" / "new"), "--json")  # fmt: skip
        (W / "results" / f"agy_{cand}_old.json").write_text(old.stdout)
        (W / "results" / f"agy_{cand}_new.json").write_text(new.stdout)
        imp = dream(f"agy_{cand}_import", "import-proof", "--bundle", str(src), "--result",
                    str(W / "results" / f"agy_{cand}_new.json"),
                    "--out", str(W / "assessments" / f"agy_{cand}.json"))  # fmt: skip
        assert imp.returncode == 0, imp.stderr
        assessment = json.loads(imp.stdout)
        summary["agy"][cand] = {
            "old_proof": {k: (v["claim_status"], v["proof_check_status"])
                          for k, v in statuses(old.stdout).items()},
            "new_proof": {k: (v["claim_status"], v["check_outcome"], v["proof_check_status"],
                              v["assurance"]["source_origin"], v["assurance"]["evidence_status"])
                          for k, v in statuses(new.stdout).items()},
            "dream_disposition": assessment["disposition"],
            "dream_reason": assessment["reason"],
        }  # fmt: skip

    # --- Claude corpus: real acquisition, then Dream -> Proof -> Dream ---------------------------
    records = acquire_all(W / "store")
    live_fetch = proof("live_fetch", "acquire", "--store", str(W / "live_store"), "--url",
                       "https://www.ruby-lang.org/en/news/", timeout=40)  # fmt: skip
    live = json.loads(live_fetch.stdout) if live_fetch.returncode == 0 else None
    summary["live_fetch"] = {
        "exit": live_fetch.returncode,
        "record": live,
        "error": live_fetch.stderr.strip() or None,
    }
    # The live record lives in its own store; copy it so one store serves the evaluation.
    if live:
        for part in ("raw", "records"):
            for f in (W / "live_store" / part).iterdir():
                shutil.copy(f, W / "store" / part / f.name)

    cand, ev = build_claude_corpus(records, live)
    (W / "inputs" / "claude_candidate.json").write_text(json.dumps(cand, indent=2))
    (W / "inputs" / "claude_evidence.json").write_text(json.dumps(ev, indent=2))
    bundle = W / "bundles" / "claude"
    exp = dream("claude_export", "export-proof", str(W / "inputs" / "claude_candidate.json"),
                "--evidence", str(W / "inputs" / "claude_evidence.json"), "--out", str(bundle))  # fmt: skip
    assert exp.returncode == 0, exp.stderr
    new = proof("claude_new", "evaluate", str(bundle), "--profile", "research", "--evidence-root",
                str(W / "proof_out" / "claude_new"), "--acquisition-store", str(W / "store"),
                "--json")  # fmt: skip
    old = old_proof("claude_old", "evaluate", str(bundle), "--profile", "research",
                    "--evidence-root", str(W / "proof_out" / "claude_old"), "--json")  # fmt: skip
    nostore = proof("claude_new_nostore", "evaluate", str(bundle), "--profile", "research",
                    "--evidence-root", str(W / "proof_out" / "claude_nostore"), "--json")  # fmt: skip
    (W / "results" / "claude_new.json").write_text(new.stdout)
    (W / "results" / "claude_old.json").write_text(old.stdout)
    (W / "results" / "claude_new_nostore.json").write_text(nostore.stdout)
    imp = dream("claude_import", "import-proof", "--bundle", str(bundle), "--result",
                str(W / "results" / "claude_new.json"),
                "--out", str(W / "assessments" / "claude.json"))  # fmt: skip
    assert imp.returncode == 0, imp.stderr
    assessment = json.loads(imp.stdout)
    again = dream("claude_import_again", "import-proof", "--bundle", str(bundle), "--result",
                  str(W / "results" / "claude_new.json"))  # fmt: skip
    summary["claude"] = {
        "old_proof": {k: v["claim_status"] for k, v in statuses(old.stdout).items()},
        "new_proof_no_store": {k: v["claim_status"] for k, v in statuses(nostore.stdout).items()},
        "new_proof": statuses(new.stdout),
        "proof_verdict": json.loads(new.stdout)["verdict"],
        "proof_deciding_rule": json.loads(new.stdout)["deciding_rule"],
        "dream_disposition": assessment["disposition"],
        "dream_reason": assessment["reason"],
        "dream_replay_identical": json.loads(again.stdout) == assessment,
        "dream_summary_row": next(e for e in assessment["evidence"]
                                  if e.get("kind") == "proof_evidence_summary"),
    }  # fmt: skip
    (W / "results" / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (LOGS / "commands.json").write_text(json.dumps(LOG, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "claude"}, indent=1, default=str)[:3000])
    print(json.dumps({k: (v if k != "new_proof" else {c: (r["claim_status"], r["check_outcome"],
          r["assurance"]["source_origin"] if r["assurance"] else None) for c, r in v.items()})
          for k, v in summary["claude"].items()}, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
