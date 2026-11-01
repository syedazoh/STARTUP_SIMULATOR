# Branch consolidation — 1 November 2026

Requested scope: test all remote branches, merge their work into `main`, and retain only `main`.

## Merge decisions

- Original main: `e129cbc06425fcba919750f4563c00e630daf30c`.
- Reliability branch `ce893f10971108c3fd792d3a3ad9128693640da1` fast-forwarded into local main.
- Consolidated security branch merged with explicit conflicts resolved against current supervised task and session behavior.
- Kept structured action schemas, CEO/owner approval, revocable sessions, upload validation, scoped frontend state, and outcome-based run reports.
- Incorporated atomic shared login throttling, finite simulation work for duration-only runs, a post-resume deadline check, and a minimum simulation interval of 0.1 seconds.
- Login now fails closed with 503 without shared MongoDB storage; five attempts per account per fixed five-minute window include successful attempts.
- Unspecified simulations default to 1,000 ticks; duration-only runs also stop at 1,000 ticks. Retained in-memory records remain independently bounded at 500.
- Existing feature/fix branch implementations were already integrated through squash merges. Historical merges preserve their commits while retaining later fixes. No older dependency/model defaults were restored.
- Local reliability commit `67162c8` had an identical tree to remote `ce893f1`; both histories are preserved.

## Verification method

Each branch gets a detached worktree. Commands: `pytest -xq` in backend, `npm test`, `npm run lint`, and `npm run build` in frontend. Backend stops on its first failure. A dummy provider key and offline model settings are used; no real provider credentials. Historical branch checks share the installed Python and Node dependencies with the current project: they are compatibility checks, not independent clean-lock installations. MongoDB behavior in tests uses doubles; browser, real Mongo, crash/restart and live provider validation remain outside these results.

## Per-branch results

| Branch | Full SHA | Backend | Frontend tests | Lint | Build |
|---|---|---|---|---|---|
| coderabbit/consolidate-changes-main/95d792ce | `13e25428e780c4234f7c87cef2bf25d24163053f` | 217 passed, 1346 warnings in 212.45s (0:03:32) | not defined | pass | pass |
| coderabbit/fix-manual-action-authorization/4df0f1dc | `261021942c7863e697c33408cde5144dbb64b71f` | 1 failed, 161 passed in 206.16s (0:03:26) | not defined | pass | pass |
| coderabbit/limit-simulation-resource-usage/dabeac91 | `121a8b510b2b97b24d507bfcd6e34241d175061a` | 198 passed in 203.77s (0:03:23) | not defined | pass | pass |
| coderabbit/throttle-login-attempts/6e3eb91f | `85ae5152b71e2503558a18d0643d0946931e0856` | 1 failed, 162 passed, 1087 warnings in 213.32s (0:03:33) | not defined | pass | pass |
| codex/startup-reliability-checklist | `ce893f10971108c3fd792d3a3ad9128693640da1` | 289 passed, 2571 warnings in 216.17s (0:03:36) | pass | pass | pass |
| feat/ceo-ledger-department-tasks | `8de764834bd83be15da340c301d807109c836779` | 267 passed, 2521 warnings in 213.32s (0:03:33) | pass | pass | pass |
| fix/ai-diagnostics | `a2323a712859eda1e31d00d54c91cfcb97cba840` | 251 passed, 2385 warnings in 210.30s (0:03:30) | pass | pass | pass |
| fix/ceo-supervision-and-execution | `9fddf6bc26f761cf31566a235f866377eb737857` | 233 passed, 2371 warnings in 205.70s (0:03:25) | pass | pass | pass |
| fix/docker-service-wiring | `33fe8dc3686f3249b472681270af167749a365f0` | exit 0 (no final pytest summary) | pass | pass | pass |
| fix/signup-login-feedback | `5b3f81422be35c5dfaaf5442d58d9aa349a9dcc2` | 267 passed, 2521 warnings in 206.16s (0:03:26) | pass | pass | pass |
| fix/tailwind-docker | `64f9338e29fde3da6970ecffd5bde8337ba7f3f9` | 238 passed, 2371 warnings in 199.89s (0:03:19) | pass | pass | pass |
| main | `e129cbc06425fcba919750f4563c00e630daf30c` | 267 passed, 2521 warnings in 202.55s (0:03:22) | pass | pass | pass |

The two historical pause/resume failures repeated in isolated rechecks (1 failed each). Current merged simulation tests pass. Historical suites use `-x` and are incomplete after their first failure.

## Final validation

- Full merged backend suite: 333 passed (179.48 seconds in final logged run).
- Focused merge regressions: 101 passed.
- Frontend: 21 tests passed, lint passed, production build passed.
- `pip check`: no broken requirements.
- `git diff --check`: passed.
- Every remote branch tip is an ancestor of the consolidated main before deletion.

Existing larger roadmap items remain tracked in `docs/IMPLEMENTATION_CHECKLIST.md`; this merge does not complete durable recovery, causal economics, outcome memory or release validation.
