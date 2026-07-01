---
name: requesting-code-review
description: Use when completing a non-trivial task, sub-task, or bug fix before committing — dispatches a code reviewer subagent to catch Critical/Important/Minor issues before they cascade into the next task. Pairs with `receiving-code-review` (the response discipline).
---

# Requesting Code Review

Dispatch a `general-purpose` subagent as a Senior Code Reviewer against a `BASE..HEAD` git range. The reviewer gets a tightly-scoped prompt (not your session history) so it stays focused on the work product.

**Core principle:** Review early, review often.

## When to Request

**Mandatory (LexPrime project rule):**

- After each subagent completes a single track / sub-task, before owner accepts
- After fixing a complex bug (cross-service contract, concurrency, init order, UTF-8 regression)
- Before merging 2+ tracks together (avoid Plan-final-report-time explosions)
- Before pushing to remote

**Optional:**

- When stuck (fresh perspective before debugging further)
- Before refactoring (baseline check)
- After perf changes

**Skip:**

- Single-file typo / comment / doc tweak (owner manual review)
- The `plan-NN-final-report.md` itself — it **is** a review document, no extra layer needed

See `.harness/AGENTS.md` "Code Review 纪律" section for the full trigger matrix.

## How to Dispatch

**1. Get SHAs:**

```bash
BASE_SHA=$(git rev-parse HEAD~1)   # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Open the template:**

Read `code-reviewer.md` (sibling file) — it has the full prompt template with placeholders.

**3. Fill placeholders:**

- `[DESCRIPTION]` — one-paragraph summary of what you built
- `[PLAN_OR_REQUIREMENTS]` — pointer to plan file (`docs/plans/plan-NN-*.yaml`) or task description
- `[BASE_SHA]` / `[HEAD_SHA]` — from step 1

**4. Spawn `general-purpose` subagent** with the filled prompt.

**5. Critical rule on the reviewer:**

The reviewer's working copy must be **read-only** on this checkout. It must NOT mutate the working tree, index, HEAD, or branch state. If it needs a different revision, it should `git worktree add /tmp/review-[SHA] [SHA]` — never move HEAD on this checkout.

## Acting on Feedback

| Severity | Action |
|---|---|
| **Critical** | Fix immediately. Block commit. |
| **Important** | Fix before proceeding to next task. |
| **Minor** | Note as TODO, don't block commit. |

**Push back when wrong:** If the reviewer's claim doesn't hold, defend with code/tests/repro — don't perform agreement. See `receiving-code-review` for the response discipline (verify → restate → push back).

## Pair With

- **`receiving-code-review`** — when YOU are the one receiving feedback (downstream skill)
- **`finishing-a-development-branch`** — when the review passes and you're ready to merge/PR/cleanup
- **`.harness/AGENTS.md`** — the project-level rules that say when to dispatch this skill

## Output Format the Reviewer Returns

```
### Strengths
[what was done well]

### Issues

#### Critical (Must Fix)
- File:line — what's wrong — why it matters — how to fix

#### Important (Should Fix)
- ...

#### Minor (Nice to Have)
- ...

### Recommendations
[process / architecture suggestions]

### Assessment
**Ready to merge?** Yes | No | With fixes
**Reasoning:** 1-2 sentences
```

## Files in this skill

```
.harness/skills/requesting-code-review/
├── SKILL.md               # this file (agentskills.io standard)
└── code-reviewer.md       # dispatch prompt template (copy-paste to subagent)
```

## Red Flags

- ❌ Skip review because "it's a small change" — **1-line edits can break cross-service contracts** (see `.harness/AGENTS.md` Critical Quirks #1)
- ❌ Ignore Critical issues
- ❌ Proceed with unfixed Important issues
- ❌ Argue with valid technical feedback without evidence
- ❌ Let the reviewer mutate your working tree

## Reference

- Original skill source: `~/.mavis/skills/requesting-code-review/SKILL.md`
- LexPrime project rules: `.harness/AGENTS.md`