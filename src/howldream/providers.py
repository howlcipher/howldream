"""Observable provider seam; no tools or private reasoning are requested."""

import http.client
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from howldream.schema import ProviderConfig


@dataclass
class Response:
    text: str
    model: str
    latency_seconds: float = 0.0
    usage: dict | None = None


class Provider(Protocol):
    capabilities: dict[str, bool]

    def generate(
        self, prompt: str, condition: str, index: int, temperature: float, seed: int
    ) -> Response: ...


CAPABILITIES = dict.fromkeys(
    [
        "supports_seed",
        "supports_logprobs",
        "supports_tool_calls",
        "supports_structured_output",
        "supports_token_usage",
        "supports_local_instrumentation",
    ],
    False,
)

IDEAS = [
    (
        "IDEA: Compare hallucination claims against a supplied source ledger.\n"
        "ASSUMPTION: source ledger coverage is sufficient."
    ),
    (
        "IDEA: Detect hallucination with metamorphic source-order tests; flag answers that change "
        "when independent evidence is permuted.\n"
        "ASSUMPTION: the question is invariant to source order."
    ),
    (
        "IDEA: Detect hallucination using executable arithmetic witnesses attached to numerical "
        "claims.\nCALC: 17 * 19 = 323\nASSUMPTION: the calculation models the intended quantity."
    ),
    (
        "IDEA: Detect hallucination through source-deletion sensitivity; remove cited evidence and "
        "measure whether confidence falls.\nASSUMPTION: confidence wording reflects uncertainty."
    ),
    (
        "IDEA: Detect hallucination by tracking qualifier loss across repeated summaries with an "
        "invariant ledger.\nASSUMPTION: the original qualifiers are correct."
    ),
    (
        "IDEA: Eliminate every hallucination by trusting a majority of models.\n"
        "FACT: model_consensus=guarantees_truth"
    ),
    "IDEA: Build an unrelated purple carousel for entertainment.",
]


class MockProvider:
    """Authored finite fixtures, not an AI model or empirical creativity claim."""

    def __init__(self):
        self.capabilities = {**CAPABILITIES, "supports_seed": True}

    def generate(self, prompt, condition, index, temperature, seed):
        text = IDEAS[0] if condition == "baseline" else IDEAS[index % len(IDEAS)]
        if condition == "nightmare":
            text += "\nFACT: invented_fact=unsupported"
        return Response(text=text, model="fixture-v1")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("provider redirects are disabled")


class HTTPProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.base = config.base_url or (
            "http://127.0.0.1:11434" if config.kind == "ollama" else "https://api.openai.com/v1"
        )
        parsed = urlsplit(self.base)
        local = parsed.hostname in {"127.0.0.1", "::1", "localhost"}
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("base_url must not contain credentials, query, or fragment")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("base_url must be an HTTP(S) origin with optional API path")
        if not local and not config.allow_remote:
            raise ValueError("remote providers require allow_remote: true")
        if not local and parsed.scheme != "https":
            raise ValueError("remote providers require HTTPS")
        self.key = (
            os.environ.get("HOWLDREAM_API_KEY", "") if config.kind == "openai_compatible" else ""
        )
        if config.kind == "openai_compatible" and not local and not self.key:
            raise ValueError("set HOWLDREAM_API_KEY for this remote provider")
        self.capabilities = {
            **CAPABILITIES,
            "supports_seed": config.kind == "ollama",
            "supports_token_usage": True,
        }
        # Ignore ambient HTTP proxies: local-only experiments stay on loopback.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def generate(self, prompt, condition, index, temperature, seed):
        config = self.config
        if config.kind == "ollama":
            endpoint = "/api/generate"
            payload = {
                "model": config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "seed": seed,
                    "num_predict": config.max_tokens,
                },
            }
        else:
            endpoint = "/chat/completions"
            payload = {
                "model": config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": config.max_tokens,
            }
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        request = urllib.request.Request(
            self.base.rstrip("/") + endpoint, data=json.dumps(payload).encode(), headers=headers
        )
        started = time.monotonic()
        try:
            with self.opener.open(request, timeout=config.timeout_seconds) as response:
                body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("provider response exceeds 2 MB")
            data = json.loads(body)
            if config.kind == "ollama":
                text = data["response"]
                usage = {
                    k: data[k] for k in ("prompt_eval_count", "eval_count") if k in data
                } or None
            else:
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("empty or non-text response")
            if usage is not None and not isinstance(usage, dict):
                raise ValueError("invalid token usage")
            model = data.get("model", config.model)
            if not isinstance(model, str):
                raise TypeError("invalid model metadata")
            return Response(text, model, time.monotonic() - started, usage)
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as error:
            # Never persist exception bodies, URLs, headers, or server echoes.
            raise ValueError(
                "provider request failed; check endpoint, model, credentials, and timeout"
            ) from error
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(
                "malformed provider response; expected a nonempty text completion"
            ) from error


def make_provider(config: ProviderConfig) -> Provider:
    return MockProvider() if config.kind == "mock" else HTTPProvider(config)
