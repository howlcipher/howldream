# HowlDream

Controlled divergent exploration for AI systems. Experimental, Phase 2 evaluation.

**Let AI dream. Decide what survives when it wakes.**

**Dream output is data, not authority.**

[Website](https://howlcipher.github.io/howldream/) ·
[Ecosystem](https://howlcipher.github.io/howl/ecosystem.html) ·
[CI](https://github.com/howlcipher/howldream/actions/workflows/ci.yml)

## DREAM / NIGHTMARE / WAKE

| State | What it does |
| --- | --- |
| DREAM | Generates divergent proposals beside a conventional baseline; all start UNVERIFIED |
| NIGHTMARE | Perturbs context or injects explicitly untrusted premises to stress reliability |
| WAKE | Checks supplied fact records, source IDs and arithmetic; preserves unresolved claims |

HowlDream is an experimental laboratory, not a truth oracle. HowlCreate already
performs creative search; HowlDream adds controlled conditions, failure analysis,
comparative measurements, and inspectable experiment records.

## Quick start

```bash
git clone https://github.com/howlcipher/howldream.git
cd howldream
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
howldream validate examples/self_detection.yaml
howldream run examples/self_detection.yaml
howldream benchmark list
howldream benchmark run dreambench --split development
howldream evaluate dreamvalue
```

No credentials or network inference are needed for the deterministic demo. Its
authored catalog is clearly labeled, not presented as AI discovery. Optional
Ollama and compatible HTTP providers support actual model experiments.

The CLI prints its artifact directory. Use that path with `inspect`, `wake`,
`replay`, `report`, and `compare`. `dream` and `nightmare` save generation for
later WAKE; `run` executes the whole pipeline. `--output` selects artifact storage.

## Measured evaluation

DreamBench 0.2.0 contains 156 authored, template-derived cases and 312 claim
annotations across four explicit splits. The primary held-out split produced
0 TP, 0 FP, 65 TN, and 13 FN: extraction coverage was 0.6667 and recall was 0.
The untouched confirmation split produced 13 TP, 0 FP, 39 TN, and 0 FN, while
exact category recall was only 0.3846. The partition gap shows phrasing sensitivity.

DreamValue 0.1.0 defines transparent conceptual-cluster, duplicate, unsupported,
INVESTIGATE, verification-survival, and Verified Novel Candidate Yield metrics.
Its 24-task equal-budget pools calibrate the evaluator; authored labels have not
received independent review, so they do not demonstrate a live DREAM advantage.
The promotion decision is HOLD. See the [report](docs/milestone_two_report.md) and
[canonical artifacts](evaluation/results/).

A local Ollama dogfood run produced mean pairwise lexical distances of 0.5824
(three baseline outputs, temperature 0.2) and 0.8510 (five DREAM outputs,
temperature 1.2 plus a premise challenge). All proposals remained unverified.
See [dogfood findings](docs/dogfood.md) and the [raw evidence](dogfood/).

## What exists

Strict versioned YAML/JSON experiments, bounded trials, provider capability records,
baseline/control runs, four context perturbations, claim grammar, extensible failure
taxonomy, exact arithmetic and supplied-ledger checks, modular scorer interface,
lexical diversity/novelty, duplicate grouping, reports, replay lineage, and advisory
handoffs. No generated code execution or hidden reasoning capture.

Final dogfood strengthened relevance triage: common function words no longer make
an unrelated proposal worth investigating. Historical artifacts retain the earlier
scores; new runs record the corrected implementation hash.

## Documentation

* [Architecture and alternatives](docs/architecture.md)
* [Experiment fields and CLI reference](docs/experiments.md)
* [Providers and observable telemetry](docs/providers.md)
* [Trust, security, privacy and limitations](docs/trust_privacy.md)
* [DreamBench and DreamValue methodology](docs/benchmarks.md)
* [Milestone Two evaluation report](docs/milestone_two_report.md)
* [Ecosystem audit and contracts](docs/ecosystem.md)
* [Roadmap](ROADMAP.md)
* [Verification evidence](docs/validation.md)

## Development

```bash
pip install -e '.[dev]'
ruff format --check src tests scripts
ruff check src tests scripts
flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
mypy
pytest -q
howldream benchmark run dreambench --split development
howldream evaluate dreamvalue
python -m build
bandit -r src -ll
pip-audit --skip-editable
python -m playwright install chromium
python scripts/check_site.py
```

Artifacts can contain sensitive source material. Storage is local plaintext,
redaction is best effort, and text retention can be disabled. Real-provider
replay repeats configuration, not guaranteed output. HowlDream is not included
in the default Howl installer. MIT licensed; experimental, not production-ready.
