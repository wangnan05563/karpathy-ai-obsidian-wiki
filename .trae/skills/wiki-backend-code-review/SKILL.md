---
name: wiki-backend-code-review
description: "Review Fastify + TypeScript backend code. Covers SSE streaming, filesystem safety, route design, harness integration, security, error handling, config management, data consistency, and session state. All configurable parameters are loaded from config/review-config.md -- no hardcoding in rule files."
---

# Wiki Backend Code Review

## Review Modes

Choose the mode from the user's request:

- **Pending-change**: review staged/working-tree files slated for commit
- **Snippet**: review pasted code excerpts (function/class/module)
- **File-focused**: review specific files or directories the user points to

Scope tightly: review only what the user provided or explicitly referenced.

## Step-by-Step Workflow

1. **Detect review mode** from user input (pending-change / snippet / file-focused).
2. **Load config**: read [config/review-config.md](config/review-config.md) for directory mappings, SSE conventions, concurrency thresholds, path traversal rules, and other parameters. Rule files never hardcode values -- all config comes from this file.
3. **Load rules index**: read [references/.rules-index.md](references/.rules-index.md) for the compact summary of all rule files with trigger keywords and core checks.
4. **Feature-scan the code**: scan review scope for trigger keywords from the index. Match patterns to rule files.
5. **Load only matched rule files** from [references/](references/) -- skip categories not triggered.
6. **Apply all matched rules** to the review scope. Each rule file defines rules with severity (critical/suggestion/best-practice), description, and suggested fix with TypeScript examples.
7. **If no rule matches**, fall back to the Generic Safety Net (below) for a best-effort review.
8. **Compose output** following the Condensed Output Format (below).

## Feature Scan

See [references/.rules-index.md](references/.rules-index.md) for the complete list of trigger keywords per rule file. Quick reference:

| Category | Key Triggers |
|----------|-------------|
| SSE streaming | 	ext/event-stream, eply.raw.write/writeHead |
| Filesystem / Vault | s/promises, index.md/log.md, FileStateStore, ault/ |
| Route design | equest.body/query/params, Content-Type, Fastify routes |
| Harness integration | EngineAdapter, AsyncIterable, yield, eforeLoop/fterLoop |
| Security | API key refs, path.join from user input, execFile/spawn, pp.listen |
| Error handling | 	ry/catch, instanceof Error, error events, state file corruption |
| Config management | eset-config, estore, updateConfig(), preset lists |
| Data consistency | display, rand, 
ormalize, 	ask_links |
| Session state | invalidate_cache, cookie, session, health check endpoints |
| Persistence & cache | import.meta.url, process.cwd(), refreshConfigCache, request.params.id, path.join, localStorage, IndexedDB, data/conversations, .gitignore |

## Generic Safety Net

If no rule matches, perform best-effort review on: **Security** (hardcoded keys, path traversal, command injection, improper binding, error info leakage), **Performance** (sync FS APIs, missing locks, unclosed SSE connections, missing budget checks), **Code Quality** (SRP violations, inconsistent signatures, inline prompts, magic strings), **Testing** (missing coverage, implementation-detail tests, flaky patterns, missing edge cases).

## Condensed Output Format

When findings exist, use **Template A (Condensed)**. When no issues, use **Template B**.

### Template A (Condensed)

`
# Code Review Summary

## Critical (<X> issues)

### 1. <brief title>

**File:** <path>:<line>
`	s
<relevant code, max 3 lines>
`

**Issue:** <one-sentence explanation with rule reference>
**Fix:** <one-line suggestion>. [Code example only if non-trivial]

---
[repeat for each issue]

## Suggestions (<Y>)
[same condensed format]

## Nits (<Z>)
[same condensed format]

## What's Good
- <positive feedback, max 3 points>
`

Rules:
- Omit any section with zero items.
- If any category has 10+ items, summarize as "10+" and show the first 10.
- Keep blank lines between sections for readability.
- If issues require code changes, append: "Would you like me to apply the suggested fix(es)?"

### Template B (No Issues)

`
## Code Review Summary
No issues found.
`

## Usage Notes

- Always include actionable fixes with code snippets when applicable. Rule file examples are in TypeScript.
- Rule Description fields are in Chinese to align with codebase conventions -- keep review explanations consistent.
- Use best-effort File:Line references; fall back to the most specific identifier available.
- When actual file paths differ from config directory mappings, review anyway and note the discrepancy.
- The rules index ([references/.rules-index.md](references/.rules-index.md)) provides trigger keywords and core checks for all 10 rule files. Load full rule files only for matched categories.
