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
