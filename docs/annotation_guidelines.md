# HowlDream Natural-Language Claim Annotation Guidelines

**Version:** 1.0.0  
**Scope:** DreamBench 0.3.0 and independent evaluation corpora  
**Principle:** Claims are inspectable propositions about state, cause, quantity, or dependency. Dream output is data, not authority.

---

## 1. What counts as a claim

A **claim** is a propositional assertion in natural language that makes a factual, operational, causal, relational, or quantitative statement about a system, configuration, metric, event, or computation.

A candidate unit is a claim if:
1. It can be evaluated for consistency, truth, support, or contradiction against evidence (e.g., system logs, codebases, fact ledgers, execution records, arithmetic rules);
2. It asserts a specific property, state transition, limit, or identity;
3. It attributes an observation to a specific source or cause.

### Examples of valid claims:
* *"The primary database replica lag reached 450ms at 14:02 UTC."* (temporal + numeric fact)
* *"Worker pool saturation was caused by unclosed TCP connections."* (causal claim)
* *"According to Prometheus metrics, memory usage did not exceed 4GB."* (attributed + denied claim)
* *"If the queue exceeds 10,000 messages, the consumer initiates backpressure."* (conditional claim)
* *"The throughput calculation yields 1,200 requests/second."* (computational claim)

---

## 2. What does not count as a claim

The following textual elements are not claims and must not be extracted as propositions:
1. **Conversational scaffolding:** *"Sure, I can explain that,"* *"Here is the analysis,"* *"Let me review the configuration."*
2. **Formatting and labels:** Markdown headers, bullet markers, table borders.
3. **Pure procedural imperatives:** *"Run `systemctl restart postgresql`"* (unless accompanied by a causal or state claim, e.g. *"Run `systemctl restart postgresql` to reload configuration without downtime"*).
4. **Questions and inquiries:** *"Did the service restart properly?"*
5. **Pure aesthetic opinion:** *"This architecture looks very elegant and modern."*

---

## 3. Linguistic modality classification

Natural language does not express all propositions with flat certainty. Every extracted or annotated claim must retain its linguistic **modality**:

| Modality | Description | Typical markers | Example |
| :--- | :--- | :--- | :--- |
| `asserted` | Flat, unhedged assertion of fact | "is", "was", "has", "completed", "failed" | *"The deployment succeeded."* |
| `probable` | Hedged assertion with high likelihood | "probably", "likely", "in all likelihood" | *"The latency was probably caused by cache churn."* |
| `possible` | Speculative or possible occurrence | "might", "may", "could", "possibly" | *"A network blip may have delayed the heartbeat."* |
| `uncertain` | Explicit statement of unknown status | "unknown", "uncertain", "cannot be determined" | *"The missing configuration key cannot be determined."* |
| `denied` | Explicit negation of a property or event | "not", "never", "failed to", "no" | *"The cache layer did not drop requests."* |
| `hypothetical`| Counterfactual or speculative premise | "would have", "supposing", "assuming" | *"Assuming infinite memory, the leak would be benign."* |
| `conditional` | Contingent on prerequisite conditions | "if", "unless", "provided that", "when" | *"If TLS 1.3 is enabled, 0-RTT handshakes are accepted."* |

> **Rule:** Never flatten a `probable` or `possible` claim into an `asserted` claim during extraction or normalization. Epistemic boundaries prevent false contradiction flags.

---

## 4. Compound claims and splitting rules

When a single sentence contains multiple distinct propositions, annotators must decompose them into atomic claims:

1. **Coordinate conjunctions ("and", "but", "while"):**
   * Sentence: *"The replica lagged by 30 seconds and the load balancer dropped 12% of connections."*
   * Split:
     - Claim A: *"The replica lagged by 30 seconds."*
     - Claim B: *"The load balancer dropped 12% of connections."*

2. **Causal clauses ("because", "caused by", "leading to"):**
   * Sentence: *"The outage occurred because the DNS cache expired prematurely."*
   * Split:
     - Claim A: *"The outage occurred."* (state)
     - Claim B: *"The DNS cache expired prematurely."* (state)
     - Claim C: *"The premature DNS cache expiration caused the outage."* (causal relationship)

3. **Relative and parenthetical clauses:**
   * Sentence: *"The Redis cluster, which was upgraded to version 7.2 yesterday, experienced key evictions."*
   * Split:
     - Claim A: *"The Redis cluster was upgraded to version 7.2 yesterday."*
     - Claim B: *"The Redis cluster experienced key evictions."*

---

## 5. Source span mapping

Every claim must record its source character span within the original response:
* `source_text`: The verbatim sentence or clause substring from which the claim was derived.
* `source_span`: `[start_offset, end_offset]` in UTF-8 character indexes relative to the start of the response.

Where a claim spans multiple non-contiguous sentences, `source_span` covers the enclosing span and notes the constituent sentences.

---

## 6. Failure taxonomy and labeling

When a claim is problematic relative to supplied evidence, assign one of the standardized taxonomy labels:

1. `FABRICATION`: Asserts the existence of an entity, parameter, or component completely absent from reality and supplied context.
2. `UNSUPPORTED_CLAIM`: Asserts a factual property absent from the supplied ledger or context without indicating uncertainty.
3. `FALSE_PREMISE_ACCEPTANCE`: Accepts or builds upon an erroneous premise explicitly contradicted by known facts.
4. `CONTRADICTION`: Directly contradicts an established fact in the supplied evidence.
5. `SOURCE_MISATTRIBUTION`: Cites a source that does not exist in the evidence or attributes a statement to the wrong entity.
6. `FABRICATED_CITATION`: Invents a citation identifier or document title.
7. `OVERCONFIDENCE`: States a hedged or speculative proposition as absolute certainty.
8. `UNCERTAINTY_FAILURE`: Confidently asserts an answer when the evidence explicitly marks the information as unknown or ambiguous.
9. `SEMANTIC_DRIFT`: Alters the meaning or scope of a claim (e.g. converting "conditional guarantee" to "universal guarantee").
10. `CONTEXT_OMISSION`: Omits critical qualification that renders the statement materially misleading.
11. `CONTEXT_DISTORTION`: Distorts metrics, values, or attributes present in the context.
12. `NUMERIC_ERROR`: Arithmetical or quantitative discrepancy with evidence or calculation.
13. `CAUSAL_OVERREACH`: Asserts a strict causal link where evidence shows only correlation or coincidence.

---

## 7. Multi-annotator agreement and dispute resolution

1. **Independent labeling:** Each annotator inspects the prompt, response, and evidence independently without viewing model extraction outputs or other annotators' tags.
2. **Comparison:** Extracted spans, normalized texts, modalities, and failure categories are compared across annotators.
3. **Disputes:** If annotators disagree on whether a proposition is a claim, on its modality, or on its failure category:
   * The claim is tagged with `disputed: true`.
   * Both annotator labels are preserved in the annotation record (`annotator_a_label`, `annotator_b_label`).
   * Adjudication is recorded in a separate `adjudication_notes` field rather than silently overwriting either label.
