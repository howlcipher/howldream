# Providers and observable telemetry

`mock` is a deterministic, authored seven-entry catalog. It supports offline demos,
fixtures, and CI. It ignores prompt semantics and temperature; its output difference
between conditions is deliberately scripted. It must never be represented as measured
model creativity or a discovery made by AI.

`ollama` sends local requests to `http://127.0.0.1:11434/api/generate`. Select a model
actually installed on your machine; `examples/local_dogfood.yaml` records the one used
during development. It sends temperature, seed, and a finite output-token budget.

`openai_compatible` supports chat-completions-style APIs. Configure a model supported
by the chosen endpoint. There is no claim that every model supports this parameter set.

```yaml
provider:
  kind: openai_compatible
  model: YOUR_CONFIGURED_MODEL
  base_url: https://YOUR_ENDPOINT/v1
  allow_remote: true
  timeout_seconds: 120
  max_tokens: 512
```

Supply `HOWLDREAM_API_KEY` through your environment, never YAML. A remote compatible
endpoint requires it; loopback compatible endpoints may run without a key. Remote
requests require HTTPS and `allow_remote: true`. Credentials embedded in URLs, query
strings, fragments, redirects, and ambient HTTP proxies are rejected or disabled.
Local-only means application-level loopback targeting, not an OS sandbox; a local
server can itself relay data. No external inference runs by default.

Capabilities are explicit booleans. Mock exposes seed support; Ollama exposes seed
and token-usage support; compatible APIs expose usage support but no seed guarantee.
All currently advertise no tools, logprobs, structured-output enforcement, or local
instrumentation. Missing usage is null, not zero. Latency is observed wall time.
Hosted private reasoning is neither requested nor captured. Future local instrumentation
may expose logits, entropy, probes, or activations; none is implemented now.

## Restrictive policy and remote commands (0.4.4)

Local providers now require `allow_local_inference: true`. For exploration requests,
permission is also required in the budget. `HOWL_FORBID_LOCAL_INFERENCE=1` and
`forbid_local_inference: true` always override opt-in. Selection never discovers or
launches services. `explore` uses the explicitly supplied provider configuration;
it no longer infers Ollama from `local_only: false`. Provider allowlists authorize
choices; they are not requests to execute each listed provider.

Shared policy and guarded transport live in howl-provider-core. Proxies and
redirects are disabled, and DNS destinations are validated before connecting to
literal addresses. Non-public destinations are conservatively treated as local.
Unknown explicit kinds fail schema validation. There is no runtime provider
fallback in Dream; failures preserve partial results and return nonzero status.

Commands must be configured explicitly by the operator, never through an artifact:

```bash
HOWL_FORBID_LOCAL_INFERENCE=1 howldream run examples/self_detection.yaml \
  --command-config /operator/reviewed_remote.json --allow-remote --max-calls 1
```

A profile has `argv` array, `remote: true`, optional `env_allowlist` variable names,
`timeout_seconds` (default 120), and `max_output_bytes` (default 2 MiB per stream).
The command receives the prompt through stdin in a private temporary directory.
Audit authentication, tools, hooks, endpoint overrides and local fallback first.
`remote` is an operator declaration, not proof of arbitrary executable behavior.
No shells are invoked, stderr is not persisted, and timeout/cancellation kills
process groups. Command transport currently requires POSIX. Model, inference,
usage and cost remain unknown unless reported; requested model is distinct.

The run records actual execution metadata per candidate and total attempted calls.
`--max-calls` may reduce the existing 500-generation bound; exhaustion preserves
partial results without changing provider. For `explore`, remote command use also
requires budget.local_only=false and command in provider_allowlist. HTTP requests
can use `provider: {kind: openai_compatible, model: ..., base_url: ..., allow_remote: true}`
in the exploration request, with a matching allowlist and remote budget permission.

## Typed candidate exports and review

```bash
howldream export RUN_DIR --candidate-id CANDIDATE_ID --format howl.candidate/v1
howldream review candidate.json --evidence supplied_ledger.json
```

Exports preserve identity, claims, provider execution and linked checks from ordinary
runs or exploration envelopes. Reviews retain the complete source and append scoped
verification without changing authorship. Create exports candidates with
`howlcreate export RUN --target dream --candidate-id IDEA_ID`.
`source_candidates` in an exploration request supplies unverified challenge context,
not evidence. Generated FACT text is never itself a verified constraint: only
successful linked checks establish a constraint within their stated scope.
