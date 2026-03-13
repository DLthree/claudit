# Skill Evals — Iteration 1 Progress

**Date:** 2026-03-13
**Skills evaluated:** index, graph, path, highlight, harness
**Sample project:** `sample-uaa` (Cloud Foundry UAA — Java/Spring, ~12K symbols)

---

## Status

| Eval | With Skill | Without Skill | Notes |
|------|-----------|---------------|-------|
| eval-index-explore | ✅ complete | ❌ rate limited | |
| eval-index-lookup | ✅ complete | ✅ complete | |
| eval-graph-callees | ✅ complete | ✅ complete | |
| eval-graph-callers | ✅ complete | ❌ rate limited | |
| eval-path-security | ✅ complete | ✅ complete | |
| eval-path-java-gap | ✅ complete | ✅ complete | |
| eval-highlight-path | ✅ complete | ✅ complete | |
| eval-highlight-function | ✅ complete | ✅ complete | |
| eval-harness-fuzz | ❌ rate limited | ❌ rate limited | Need iteration 2 |
| eval-harness-extract | ❌ rate limited | ❌ rate limited | Need iteration 2 |

**Complete pairs (both sides evaluated):** 6 of 10
**Harness evals:** all 4 rate-limited — need simpler prompts or smaller project for iteration 2

---

## Assertion Pass Rates (complete pairs only)

| Eval | With Skill | Without Skill | Delta |
|------|-----------|---------------|-------|
| index-lookup | 3/3 (100%) | 1/3 (33%) | +67% |
| graph-callees | 3/3 (100%) | 1/3 (33%) | +67% |
| path-security | 3/3 (100%) | 0/3 (0%) | +100% |
| path-java-gap | 3/3 (100%) | 0/3 (0%) | +100% |
| highlight-path | 3/3 (100%) | 0/3 (0%) | +100% |
| highlight-function | 3/3 (100%) | 0/3 (0%) | +100% |

**Overall with-skill pass rate:** 18/18 = **100%**
**Overall without-skill pass rate:** 2/18 = **11%**

---

## Key Findings

### Skills are strongly discriminative

With-skill agents consistently used the correct `claudit` CLI commands and workflows. Without-skill agents fell back to manual grep/source reading every time, which:
- Fails to use `claudit` tools (assertion failures)
- Costs 2–5× more tokens
- Misses important context (interface/impl gap, Results Format output)

### Highlight skills: clearest win

The `highlight` skill had the most dramatic improvement. Without-skill agents:
- Produced **no highlighted output at all** for either prompt
- Did thorough textual descriptions instead
- Used 2–3× more tokens than needed

The skill teaches the agent that the output *format* matters (JSON Results Format / VS Code extension), not just locating the source.

### Path skill fallback workflow works

Both `eval-path-security` and `eval-path-java-gap` hit the Java interface→impl gap (0 paths from `claudit path find`). The with-skill agent correctly:
1. Tried `claudit path find` first
2. Fell back to `graph callees` + `graph callers`
3. Read source to confirm the missing edge
4. Reached the correct conclusion and noted the limitation

Without-skill agents jumped straight to manual source reading and never diagnosed the gap.

### Flag placement: skill prevents a common mistake

`eval-graph-callees` WITH skill correctly avoided passing `--language` to `graph callees`/`graph callers`. This is a known footgun documented in the graph skill.

### Token efficiency

| Eval | With tokens | Without tokens | Ratio |
|------|------------|----------------|-------|
| path-security | 31,509 | 63,157 | 0.50× (2× cheaper) |
| path-java-gap | 23,028 | 37,232 | 0.62× |
| highlight-function | 13,516 | 21,784 | 0.62× |
| graph-callees | 15,862 | 22,562 | 0.70× |

Skills reduce token usage by **30–50%** on average for complex analysis tasks.

---

## Concerns / Items to Address

### 1. eval prompts used function names that don't exist
`createScimGroup` is a Spring REST Docs string label, not a real method. This caused `graph callees` to return 0 (correct, but potentially confusing). Future eval prompts should use real method names like `createGroup` (in `ScimGroupEndpoints`) or `validateGroup` (in `JdbcScimGroupProvisioning`).

### 2. Harness evals hit rate limits every time
The harness workflow is too heavy for the current subagent rate limit (42–55 tool uses before hitting limits). For iteration 2:
- Use a smaller sample project (e.g., a C file from the codebase, not the full Java UAA)
- Or split harness eval into two: one for extraction, one for dependency analysis

### 3. index-explore without-skill: rate limited too
Without-skill on the open-ended "give me an overview" prompt ran 55+ tool uses. Consider bounding the prompt.

---

## Next Steps

1. **Iteration 2:** Re-run harness evals with smaller scope (C project or single Java file)
2. **Description optimization:** Run `scripts/run_loop.py` on the updated skill descriptions
3. **Eval prompts fix:** Replace `createScimGroup` with `createGroup` or `validateGroup` in graph evals
