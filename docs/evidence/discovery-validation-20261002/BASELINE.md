# Baseline

Safety: every Python/test/provider invocation sets HOWL_FORBID_LOCAL_INFERENCE=1.
No local generative inference authorized or performed.

| Repository | Start branch | Start SHA | Status | Fetch/pull |
| --- | --- | --- | --- | --- |
| howldream | main | dd2cc52b82b4fefa8273a4db9abc709fef22d35f | clean | fetched; ff-only already current |
| howlcreate | main | 63850ef45378f5bc35ba8fe7eff4a50cd74010d6 | clean | fetched; ff-only already current |
| howl-provider-core | main | d0054c46255dbefbf8865baab45d0fc7c9530eba | clean | fetched; ff-only already current |

Isolated worktrees: worktrees/discovery-dream and worktrees/discovery-create;
branch hardening/discovery-validation in each. Provider-core read/test only.
Rules read: workspace .agents/rules/engineering-task-completion.md, Dream AGENTS.md,
and canonical anti_manipulation.md at /home/howlcipher/howlcipher/howlplane/.agents/rules/.
The workspace has no skills directory; installed per-entry skills are used.
Initial shared-venv Dream/Create collection lacked sibling provider-core imports;
rerun with explicit PYTHONPATH, not treated as application regression.

Reproduction: reproduce.py and reproduction-baseline.json, using deterministic fixtures.
Original baseball artifacts are read-only historical evidence.
