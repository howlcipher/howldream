"""Shared ecosystem exploration schemas, authority models, and descent DAG."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ExplorationAuthority(StrictModel):
    """Explicit authority boundary. HowlDream artifacts cannot authorize execution."""

    type: Literal["ADVISORY"] = "ADVISORY"
    executable: Literal[False] = False

    @model_validator(mode="after")
    def fail_closed_on_authority(self) -> ExplorationAuthority:
        if self.type != "ADVISORY" or self.executable is not False:
            raise ValueError(
                "HowlDream requires authority.type='ADVISORY' and authority.executable=False"
            )
        return self


class ExplorationBudget(StrictModel):
    """Finite bounded resource budget for speculative exploration."""

    max_candidates: int = Field(default=6, ge=1, le=50)
    max_trials: int = Field(default=1, ge=1, le=10)
    max_tokens: int = Field(default=512, ge=32, le=4096)
    max_duration_seconds: int = Field(default=120, ge=1, le=600)
    provider_allowlist: list[str] = Field(default_factory=lambda: ["mock", "ollama"])
    local_only: bool = True


class EvidenceRef(StrictModel):
    """Evidence supplied to or extracted during exploration."""

    id: str = Field(pattern=r"^[a-zA-Z0-9_./-]{1,100}$")
    text: str = Field(default="", max_length=50000)
    facts: dict[str, str] = Field(default_factory=dict)


class Provenance(BaseModel):
    """Shared audit-trail metadata attached to every howl.* envelope.

    Deliberately open (extra="allow"), unlike StrictModel: provenance is
    descriptive audit metadata, not an authority or structural boundary, and
    producers have historically attached ad hoc extra keys (e.g. request-
    specific hashes). The named fields below are the canonical, cross-cutting
    concepts every producer should populate; anything else stays as an
    unvalidated extra key rather than failing validation.

    Concepts deliberately NOT duplicated here because a dedicated top-level
    field already covers them on the envelopes that need them: authority
    state (`authority`), schema identity (`schema_version`), candidate/run
    lineage (`parent_request_id`, `source_run_id`, `candidate_id`,
    `descent_dag`), and per-envelope evaluation/verification state
    (`CandidateHandoff.status`, `CandidateAssessment.disposition`,
    `ExplorationResult.verification_status`).
    """

    model_config = ConfigDict(extra="allow")

    run_id: str | None = None
    producer_component: str | None = None
    producer_version: str | None = None
    model_or_provider: str | None = None
    observation_kind: (
        Literal["SIMULATED", "DETERMINISTIC", "LIVE", "EXTERNALLY_OBSERVED"] | None
    ) = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    transformations: list[str] = Field(default_factory=list)


class ExplorationRequest(StrictModel):
    """Standardized machine-readable exploration envelope: howl.exploration/v1."""

    schema_version: Literal["howl.exploration/v1"] = "howl.exploration/v1"
    request_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    parent_run_id: str | None = None
    objective: str = Field(min_length=1, max_length=10000)
    originating_component: str = Field(default="howlplane", min_length=1, max_length=100)
    requested_mode: Literal["dream", "nightmare", "paired"] = "dream"
    constraints: list[str] = Field(default_factory=list, max_length=50)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list, max_length=100)
    context_refs: list[str] = Field(default_factory=list, max_length=20)
    risk_class: str = Field(default="EXPLORATORY", max_length=50)
    authority: ExplorationAuthority = Field(default_factory=ExplorationAuthority)
    budget: ExplorationBudget = Field(default_factory=ExplorationBudget)
    provenance: Provenance = Field(default_factory=Provenance)

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("request_id cannot be empty")
        return v


class CandidateHandoff(StrictModel):
    """Speculative candidate for cross-component evaluation: howl.candidate/v1."""

    schema_version: Literal["howl.candidate/v1"] = "howl.candidate/v1"
    candidate_id: str = Field(min_length=1, max_length=200)
    source_run_id: str = Field(min_length=1, max_length=100)
    parent_request_id: str = Field(min_length=1, max_length=100)
    objective: str = Field(min_length=1, max_length=10000)
    text: str = Field(min_length=1, max_length=50000)
    condition: str = Field(default="dream")
    trust: Literal["UNVERIFIED"] = "UNVERIFIED"
    status: Literal[
        "GENERATED",
        "CHALLENGED",
        "LOCALLY_VERIFIED",
        "FRAME_REVIEWED",
        "UNRESOLVED",
        "REJECTED",
    ] = "GENERATED"
    authority: ExplorationAuthority = Field(default_factory=ExplorationAuthority)
    claims: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_issues: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    verified_constraints: list[str] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)


class CandidateAssessment(StrictModel):
    """Downstream evaluation result from HowlFrame: howl.assessment/v1."""

    schema_version: Literal["howl.assessment/v1"] = "howl.assessment/v1"
    assessment_id: str = Field(min_length=1, max_length=100)
    candidate_id: str = Field(min_length=1, max_length=200)
    disposition: Literal["REJECT", "UNRESOLVED", "INVESTIGATE", "ACCEPT_FOR_DEVELOPMENT"]
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_claims: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"] = "LOW"
    limitations: list[str] = Field(default_factory=list)
    authority: ExplorationAuthority = Field(default_factory=ExplorationAuthority)
    provenance: Provenance = Field(default_factory=Provenance)


class DevelopmentResult(StrictModel):
    """Deliberate sandbox prototype specification from HowlCreate: howl.development_result/v1."""

    schema_version: Literal["howl.development_result/v1"] = "howl.development_result/v1"
    development_id: str = Field(min_length=1, max_length=200)
    source_candidate_id: str = Field(min_length=1, max_length=200)
    parent_request_id: str = Field(min_length=1, max_length=100)
    origin: str = Field(default="howldream", min_length=1, max_length=100)
    epistemic_status: str = Field(min_length=1, max_length=100)
    authority: ExplorationAuthority = Field(default_factory=ExplorationAuthority)
    execution_authority: Literal["NONE"] = "NONE"
    idea: dict[str, Any] = Field(default_factory=dict)
    lineage: dict[str, Any] = Field(default_factory=dict)
    sandbox_prototype_design: dict[str, Any] = Field(default_factory=dict)
    test_specification: list[dict[str, Any]] = Field(default_factory=list)
    architecture_proposal: str = Field(default="", max_length=100000)
    provenance: Provenance = Field(default_factory=Provenance)


class DescentNode(StrictModel):
    """Single node in the durable descent DAG."""

    node_id: str = Field(min_length=1, max_length=200)
    node_type: Literal[
        "OBJECTIVE",
        "BASELINE",
        "DREAM_RUN",
        "CANDIDATE",
        "NIGHTMARE_CHALLENGE",
        "WAKE_VERIFICATION",
        "FRAME_ASSESSMENT",
        "CREATE_PROJECT",
    ]
    label: str = Field(min_length=1, max_length=500)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class DescentEdge(StrictModel):
    """Directed derivation edge in the descent DAG."""

    source: str = Field(min_length=1, max_length=200)
    target: str = Field(min_length=1, max_length=200)
    relation: str = Field(min_length=1, max_length=100)


class DescentDAG(StrictModel):
    """Durable lineage DAG recording exploration descent and surviving handoffs."""

    nodes: dict[str, DescentNode] = Field(default_factory=dict)
    edges: list[DescentEdge] = Field(default_factory=list)
    max_depth: int = Field(default=20, ge=1, le=100)
    max_branching_factor: int = Field(default=50, ge=1, le=200)

    def is_reachable(self, start: str, target: str) -> bool:
        """Check if target is reachable from start via directed edges."""
        visited: set[str] = set()
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr == target:
                return True
            if curr in visited:
                continue
            visited.add(curr)
            for edge in self.edges:
                if edge.source == curr and edge.target not in visited:
                    queue.append(edge.target)
        return False

    def add_node(self, node: DescentNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str, relation: str) -> None:
        if source == target:
            raise ValueError(f"Lineage cycle detected: self-loop on node '{source}'")

        # Idempotency check: if edge already exists, no-op
        for edge in self.edges:
            if edge.source == source and edge.target == target and edge.relation == relation:
                return

        # Cycle check: adding source -> target creates cycle if source is reachable from target
        if self.is_reachable(target, source):
            raise ValueError(
                f"Lineage cycle detected: edge '{source}' -> '{target}' would create a cycle"
            )

        # Branching factor check: out-degree of source
        out_degree = sum(1 for e in self.edges if e.source == source)
        if out_degree >= self.max_branching_factor:
            raise ValueError(
                f"Lineage branching overflow: node '{source}' "
                f"exceeds max branching factor {self.max_branching_factor}"
            )

        # Depth check: compute max depth from any root to target
        self.edges.append(DescentEdge(source=source, target=target, relation=relation))
        depth = self._compute_max_depth(target)
        if depth > self.max_depth:
            self.edges.pop()
            raise ValueError(
                f"Lineage depth overflow: target '{target}' "
                f"reaches depth {depth} > max_depth {self.max_depth}"
            )

    def _compute_max_depth(self, node_id: str) -> int:
        """Calculates the longest path from any root ancestor to node_id."""
        memo: dict[str, int] = {}

        def _get_depth(curr: str, path: set[str]) -> int:
            if curr in memo:
                return memo[curr]
            if curr in path:
                return 0
            path.add(curr)
            incoming = [e.source for e in self.edges if e.target == curr]
            if not incoming:
                max_d = 1
            else:
                max_d = 1 + max((_get_depth(src, path) for src in incoming), default=0)
            path.remove(curr)
            memo[curr] = max_d
            return max_d

        return _get_depth(node_id, set())

    def trace(self, start_id: str) -> list[DescentNode]:
        """Traverse backwards from start_id to the root objective node."""
        visited: set[str] = set()
        chain: list[DescentNode] = []

        def _walk(curr: str):
            if curr in visited or curr not in self.nodes:
                return
            visited.add(curr)
            chain.append(self.nodes[curr])
            for edge in self.edges:
                if edge.target == curr:
                    _walk(edge.source)

        _walk(start_id)
        return chain


class ExplorationResult(StrictModel):
    """Complete machine-readable outcome returned by HowlDream: howl.exploration_result/v1."""

    schema_version: Literal["howl.exploration_result/v1"] = "howl.exploration_result/v1"
    exploration_id: str = Field(min_length=1, max_length=100)
    parent_request_id: str = Field(min_length=1, max_length=100)
    objective: str = Field(min_length=1, max_length=10000)
    originating_component: str = Field(min_length=1, max_length=100)
    authority: ExplorationAuthority = Field(default_factory=ExplorationAuthority)
    candidates: list[CandidateHandoff] = Field(default_factory=list)
    claims: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_assumptions: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    scores: list[dict[str, Any]] = Field(default_factory=list)
    verification_status: Literal["UNVERIFIED", "REQUIRES_DOWNSTREAM_REVIEW", "LOCALLY_VERIFIED"] = (
        "UNVERIFIED"
    )
    recommended_disposition: Literal["INVESTIGATE", "REJECT", "DEFER", "ACCEPT_FOR_DEVELOPMENT"] = (
        "DEFER"
    )
    provenance: Provenance = Field(default_factory=Provenance)
    descent_dag: DescentDAG = Field(default_factory=DescentDAG)


def create_request_id() -> str:
    return f"req-{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
