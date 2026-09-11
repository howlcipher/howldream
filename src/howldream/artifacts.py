"""Private-by-default snapshots with integrity checks, not cryptographic attestation."""

import hashlib
import json
import os
import re
from pathlib import Path


def redact(text: str) -> str:
    patterns = [
        r"sk-[A-Za-z0-9_-]{12,}",
        r"gh[pousr]_[A-Za-z0-9_]{12,}",
        r"github_pat_[A-Za-z0-9_]+",
        r"(?i)(?:authorization[\"']?\s*[:=]\s*[\"']?)(?:bearer\s+)?[^\s,\"'}]+",
        r"(?i)(?:password|api_key|token)[\"']?\s*[:=]\s*[\"']?[^\s,\"'}]+",
        r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "[REDACTED]", text)
    return text


def scrub(value):
    if isinstance(value, str):
        # Redact the configured API key even when it does not match a known pattern.
        key = os.environ.get("HOWLDREAM_API_KEY")
        return redact(value.replace(key, "[REDACTED]") if key else value)
    if isinstance(value, dict):
        secret_keys = {"authorization", "api_key", "password", "token", "access_token"}
        return {
            scrub(k): "[REDACTED]" if str(k).lower() in secret_keys else scrub(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_json(path: Path, value):
    path.write_text(json.dumps(scrub(value), indent=2, ensure_ascii=False) + "\n")
    path.chmod(0o600)


def save_run(path: Path, artifacts: dict):
    for name, value in artifacts.items():
        if name == "manifest":
            continue
        if name in {"baseline", "candidates", "claims", "verification"}:
            target = path / f"{name}.jsonl"
            target.write_text("".join(json.dumps(scrub(row)) + "\n" for row in value))
            target.chmod(0o600)
        else:
            write_json(path / f"{name}.json", value)
    artifacts["manifest"]["file_hashes"] = {
        p.name: digest(p.read_text()) for p in sorted(path.iterdir()) if p.name != "manifest.json"
    }
    write_json(path / "manifest.json", artifacts["manifest"])


def load_run(path: Path) -> dict:
    if (path / "manifest.json").is_symlink():
        raise ValueError("invalid artifact path")
    manifest = json.loads((path / "manifest.json").read_text())
    if manifest.get("schema") != "howldream.run/v1":
        raise ValueError("unsupported run schema")
    if manifest.get("authority") != "NONE":
        raise ValueError("invalid run authority: only NONE is allowed")
    required = {
        "experiment.json",
        "baseline.jsonl",
        "candidates.jsonl",
        "claims.jsonl",
        "verification.jsonl",
        "scores.json",
        "metrics.json",
        "handoff.json",
        "report.md",
    }
    optional = {"exploration_envelope.json"}
    hashes = set(manifest.get("file_hashes", {}))
    if not required.issubset(hashes) or not hashes.issubset(required | optional):
        raise ValueError("artifact integrity index is incomplete or contains unknown files")
    for name, expected in manifest["file_hashes"].items():
        if Path(name).name != name or (path / name).is_symlink():
            raise ValueError("invalid artifact path")
        if digest((path / name).read_text()) != expected:
            raise ValueError(f"artifact integrity mismatch: {name}")
    result = {"manifest": manifest}
    for name in ("experiment", "scores", "metrics", "handoff"):
        result[name] = json.loads((path / f"{name}.json").read_text())
    if "exploration_envelope.json" in manifest["file_hashes"]:
        result["exploration_envelope"] = json.loads(
            (path / "exploration_envelope.json").read_text()
        )
    for name in ("baseline", "candidates", "claims", "verification"):
        result[name] = [
            json.loads(line) for line in (path / f"{name}.jsonl").read_text().splitlines()
        ]
    for candidate in result["baseline"] + result["candidates"]:
        if (
            not isinstance(candidate, dict)
            or candidate.get("trust") != "UNVERIFIED"
            or not isinstance(candidate.get("text"), str)
            or not isinstance(candidate.get("id"), str)
        ):
            raise ValueError("invalid candidate structure or trust state")
    return result
