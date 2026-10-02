"""Observable provider seam; no tools or private reasoning are requested."""

import http.client
import ipaddress
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from howl_provider_core import (
    CommandConfig,
    CommandProvider,
    Execution,
    Policy,
    ProviderError,
    classify_failure,
    guarded_opener,
    reported_metadata,
)

from howldream.schema import ProviderConfig


@dataclass
class Response:
    text: str
    model: str
    latency_seconds: float = 0.0
    usage: dict | None = None
    execution: dict | None = None


class Provider(Protocol):
    capabilities: dict[str, bool]

    def generate(
        self, prompt: str, condition: str, index: int, temperature: float, seed: int
    ) -> Response: ...


CAPABILITIES = dict.fromkeys(
    [
        "supports_seed",
        "supports_temperature",
        "supports_top_p",
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
        self.capabilities = dict(CAPABILITIES)

    def generate(self, prompt, condition, index, temperature, seed):
        text = IDEAS[0] if condition == "baseline" else IDEAS[index % len(IDEAS)]
        if condition == "nightmare":
            text += "\nFACT: invented_fact=unsupported"
        return Response(
            text=text,
            model="fixture-v1",
            execution=Execution(
                "mock",
                "mock",
                "mock",
                "fixture",
                model="fixture-v1",
                deterministic=True,
                mocked=True,
                inference_occurred=False,
                remote=False,
            ).to_dict(),
        )


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("provider redirects are disabled")


class HTTPProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.policy = Policy(config.allow_local_inference, config.forbid_local_inference)
        self.policy.check_provider(config.kind)
        self.base = config.base_url or (
            "http://127.0.0.1:11434" if config.kind == "ollama" else "https://api.openai.com/v1"
        )
        self.policy.check_url(self.base)
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
            "supports_temperature": True,
            "supports_token_usage": True,
        }
        # Ignore ambient HTTP proxies: local-only experiments stay on loopback.
        self.opener = guarded_opener(self.policy)

    def generate(self, prompt, condition, index, temperature, seed):
        config = self.config
        self.policy.check_provider(config.kind)
        self.policy.check_url(self.base)
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
        execution = None
        try:
            with self.opener.open(request, timeout=config.timeout_seconds) as response:
                body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("provider response exceeds 2 MB")
            data = json.loads(body)
            meta = reported_metadata(body.decode("utf-8"), "openai-json")
            execution = Execution(
                config.kind,
                config.kind,
                config.kind,
                "http",
                requested_model=config.model,
                model=meta["model"],
                usage=meta["usage"],
                request_id=meta["request_id"],
                inference_occurred=meta["inference_occurred"],
                raw_output_received=True,
                parse_status="FAILED",
                elapsed_seconds=time.monotonic() - started,
            ).to_dict()
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
            model = data.get("model") or "unknown"
            if not isinstance(model, str):
                raise TypeError("invalid model metadata")
            return Response(
                text,
                model,
                time.monotonic() - started,
                usage,
                {
                    **execution,
                    "parse_status": "VALID",
                    "usage": usage,
                    "remote": not local_endpoint(self.base),
                    "deterministic": data.get("deterministic", False),
                    "mocked": data.get("mocked", False),
                },
            )
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as error:
            # Never persist exception bodies, URLs, headers, or server echoes.
            failure = classify_failure(
                str(error.code)
                if isinstance(error, urllib.error.HTTPError)
                else "timeout"
                if isinstance(error, TimeoutError)
                else "provider unavailable"
            )
            raise ProviderError(
                "provider request failed; check endpoint, model, credentials, and timeout",
                failure=failure,
                execution=execution
                or Execution(
                    config.kind,
                    config.kind,
                    config.kind,
                    "http",
                    requested_model=config.model,
                    elapsed_seconds=time.monotonic() - started,
                ).to_dict(),
            ) from None
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise ProviderError(
                "malformed provider response; expected a nonempty text completion",
                execution=execution
                or Execution(
                    config.kind,
                    config.kind,
                    config.kind,
                    "http",
                    requested_model=config.model,
                    elapsed_seconds=time.monotonic() - started,
                    raw_output_received=True,
                    parse_status="FAILED",
                ).to_dict(),
            ) from None


def local_endpoint(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    try:
        return not ipaddress.ip_address(host).is_global
    except ValueError:
        return host == "localhost" or host.endswith((".local", ".localhost"))


class RemoteCommandProvider:
    def __init__(self, config: CommandConfig, policy: Policy | None = None):
        self.adapter = CommandProvider(config, policy)
        self.capabilities = dict(CAPABILITIES)

    def generate(self, prompt, condition, index, temperature, seed):
        text, execution = self.adapter.generate(prompt)
        return Response(
            text,
            execution.model or "unknown",
            execution.elapsed_seconds,
            usage=execution.usage,
            execution=execution.to_dict(),
        )


def make_provider(config: ProviderConfig) -> Provider:
    if config.kind == "command":
        raise ValueError("command requires explicit operator --command-config; not artifact config")
    return MockProvider() if config.kind == "mock" else HTTPProvider(config)


def sampling_record(provider, temperature, seed):
    """Requested controls and transport application are distinct observations.

    HTTP applied means sent in the request, not independently proven backend behavior.
    Command profiles have no reviewed sampling argument contract. Mock seed is fixture
    selection only and never a stochastic experiment.
    """
    record = {}
    for name, value in (("temperature", temperature), ("seed", seed), ("top_p", None)):
        supported = provider.capabilities.get("supports_" + name, False)
        record[name] = {
            "requested": value,
            "supported": supported,
            "applied": bool(supported and value is not None),
        }
    return record
