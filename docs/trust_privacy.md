# Trust, security, and privacy

**Dream output is data, not authority. Dreams can suggest. Dreams cannot authorize.**

No run result deploys, merges, deletes, sends communications, approves actions,
changes permissions, performs financial transactions, or executes generated commands.
Handoffs are advisory. Even a correct arithmetic statement cannot authorize an action.
An LLM labeling its text FACT, IDEA, SUPPORTED, or approved does not make it authoritative.

## Verification limits

The supplied ledger is an explicit input, not a retrieved or independently authenticated
source. Exact matches verify consistency with that input only. Unknown keys are
unsupported, not necessarily false. Citation checks establish ID presence, not source
existence or entailment. Missing-information abstentions remain uncertain. Arithmetic
checks numerical equality, not modeling assumptions. Unstructured claims are unresolved.
No accepted-truth state exists. Heuristic INVESTIGATE is permission to consider further
work only in prose; it is not executable permission in any downstream system.

## Storage and egress

Artifact location is printed by the CLI and configurable with `--output`. Default:
`.howldream/runs`. Run directories use mode 0700 and files 0600 on POSIX. Artifacts
are plaintext, not encrypted. Use an encrypted local volume for sensitive experiments.
No analytics, telemetry export, automatic retrieval, or remote-provider discovery occurs.
Only explicitly configured remote generation sends prompts and context externally.

Known API key, authorization, password, token, and private-key patterns are redacted;
the configured HOWLDREAM_API_KEY is also removed by exact match. These controls do
not identify every secret, personal detail, or sensitive source. Review artifacts before
sharing. Ordinary runs are gitignored. Committed dogfood contains only public synthetic
or project-authored engineering material.

`retain_text: false` suppresses experiment content, prompt/output text, claim text,
and verifier notes. Hashes, aggregate scores, configuration metadata, and IDs remain.
Replay and re-verification from those artifacts are unavailable. Input redaction also
disables original configuration replay. Hashes are provenance aids, not anonymization.

Report security issues privately through the repository's GitHub security reporting
mechanism when available. Do not put secrets into public issues.
