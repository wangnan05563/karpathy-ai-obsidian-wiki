---
name: wiki-backend-code-review
description: "Review Fastify + TypeScript backend code for the wiki project. Invoke when user asks to review, analyze, or improve backend files (e.g., .ts) under services/api/. Covers SSE streaming, filesystem safety, route design, harness integration, security, and error handling."
---

# Wiki Backend Code Review

## When to use this skill

Use this skill whenever the user asks to **review, analyze, or improve** Fastify + TypeScript backend code (e.g., `.ts`) under the `services/api/` directory of the wiki project. Supports the following review modes:

- **Pending-change review**: when the user asks to review current changes (inspect staged/working-tree files slated for commit to get the changes).
- **Code snippets review**: when the user pastes code snippets (e.g., a function/class/module excerpt) into the chat and asks for a review.
- **File-focused review**: when the user points to specific files and asks for a review of those files (one file or a small, explicit set of files, e.g., `services/api/src/routes/...`, `services/api/src/engine/...`).

Do NOT use this skill when:

- The request is about frontend code or UI (e.g., `.tsx`, `.jsx`, browser-side `.ts`, `web/`).
- The request is about prompt text content quality (e.g., `.md` files under `prompts/`) ！ that is another skill's responsibility; this skill only reviews how prompts are *referenced* from code.
- The request is about the semantic correctness of Obsidian Vault content itself ！ this skill only reviews whether *operations on the Vault* are safe.
- The request is about build config, CI scripts, or other non-business-backend code (unless it involves security or path validation).
- The user is not asking for a review/analysis/improvement of backend code.

## How to use this skill

Follow these steps when using this skill:

1. **Identify the review mode** (pending-change vs snippet vs file-focused) based on the user's input. Keep the scope tight: review only what the user provided or explicitly referenced.
2. **Read [config/review-config.md](config/review-config.md)** to obtain review parameters: project directory mapping, SSE event format conventions, concurrency control thresholds, path traversal protection rules, and applicable/non-applicable scenarios. Rule files do not hardcode any values ！ all configurable parameters live in the config.
3. **Route to rule files via the Checklist** below based on what the review scope contains (SSE streaming, filesystem/vault ops, route design, harness integration, security, error handling). Apply every matching rule file to the review scope.
4. **Fall back to General Review Rules** when no Checklist rule matches the review scope, performing a best-effort review on security/performance/code-quality/testing.
5. **Compose the final output strictly following the Required Output Format** (Template A for any findings, Template B for no issues).

Notes when using this skill:
- Always include actionable fixes or suggestions (including possible code snippets). Examples in rule files are TypeScript, matching the project backend language.
- Rule `Description` fields are written in Chinese because the project code comments are in Chinese ！ keep review explanations aligned with the codebase convention.
- Use best-effort `File:Line` references when a file path and line numbers are available; otherwise, use the most specific identifier you can.

## Checklist

- SSE streaming: if the review scope contains `text/event-stream` responses, `reply.raw.write`/`reply.raw.writeHead`, or SSE helper functions under `services/api/src/routes/`, follow [references/sse-streaming-rule.md](references/sse-streaming-rule.md) to perform the review.
- filesystem / vault operations: if the review scope contains `fs/promises` calls, `index.md` / `log.md` appends, `FileStateStore`, temporary file handling, or code under `services/api/src/vault/` or `services/api/src/state/`, follow [references/filesystem-vault-rule.md](references/filesystem-vault-rule.md) to perform the review.
- route design: if the review scope contains Fastify route registration functions, request parameter parsing, Content-Type dispatching, or handler implementations under `services/api/src/routes/`, follow [references/route-design-rule.md](references/route-design-rule.md) to perform the review.
- harness integration: if the review scope involves `EngineAdapter` implementations, `AsyncIterable` event streams, budget control, hook registration (`beforeLoop`/`afterLoop`), `FileStateStore` usage, or prompt file loading under `services/api/src/engine/` or `services/api/src/workflows/`, follow [references/harness-integration-rule.md](references/harness-integration-rule.md) to perform the review.
- security: if the review scope involves API Key references, path concatenation from user input, `execFile`/`spawn` child process calls, network binding (`app.listen`), or error response construction anywhere under `services/api/`, follow [references/security-rule.md](references/security-rule.md) to perform the review.
- error handling: if the review scope contains try/catch blocks, error response construction, SSE error events, tool execution failure handling, or state file corruption recovery under `services/api/`, follow [references/error-handling-rule.md](references/error-handling-rule.md) to perform the review.

## General Review Rules

### 1. Security Review

Check for:
- Hardcoded API keys / credentials in code
- Path traversal vulnerabilities (unvalidated user input concatenated to filesystem paths)
- Command injection (`shell: true` or string-concatenated commands)
- Improper network binding (defaulting to `0.0.0.0` instead of `127.0.0.1`)
- Error responses leaking internal paths or stack traces
- Insecure direct object references via `runId` / filenames

### 2. Performance Review

Check for:
- Synchronous filesystem APIs (`fs.readFileSync` / `fs.writeFileSync`) blocking the event loop
- Missing serialization locks on concurrent file appends (`index.md` / `log.md`)
- SSE connections not closed in `finally` (connection leaks)
- Missing budget checks leading to runaway engine calls
- Missing caching opportunities for prompt file loading

### 3. Code Quality Review

Check for:
- Business logic leaking into route handlers (SRP violations)
- Inconsistent route registration function signatures
- Inline prompt strings instead of loading from `prompts/`
- Scattered SSE string concatenation instead of a unified `send` helper
- Magic strings for event types
- Poor error object handling (`String(err)` instead of `instanceof Error` guard)
- Incomplete type coverage (`as unknown as EngineAdapter` bypassing interfaces)

### 4. Testing Review

Check for:
- Missing test coverage for new routes / adapters / hooks
- Tests that don't test behavior (only implementation details)
- Flaky test patterns (filesystem-dependent tests without temp isolation)
- Missing edge cases (budget exhausted, partial failure, corrupted state file)

## Required Output Format

When this skill invoked, the response must exactly follow one of the two templates:

### Template A (any findings)

```markdown
# Code Review Summary

Found <X> critical issues need to be fixed:

## ? Critical (Must Fix)

### 1. <brief description of the issue>

FilePath: <path> line <line>
<relevant code snippet or pointer>

#### Explanation

<detailed explanation and references of the issue>

#### Suggested Fix

1. <brief description of suggested fix>
2. <code example> (optional, omit if not applicable)

---
... (repeat for each critical issue) ...

Found <Y> suggestions for improvement:

## ? Suggestions (Should Consider)

### 1. <brief description of the suggestion>

FilePath: <path> line <line>
<relevant code snippet or pointer>

#### Explanation

<detailed explanation and references of the suggestion>

#### Suggested Fix

1. <brief description of suggested fix>
2. <code example> (optional, omit if not applicable)

---
... (repeat for each suggestion) ...

Found <Z> optional nits:

## ? Nits (Optional)
### 1. <brief description of the nit>

FilePath: <path> line <line>
<relevant code snippet or pointer>

#### Explanation

<explanation and references of the optional nit>

#### Suggested Fix

- <minor suggestions>

---
... (repeat for each nits) ...

## ? What's Good

- <Positive feedback on good patterns>
```

- If there are no critical issues or suggestions or option nits or good points, just omit that section.
- If the issue number is more than 10, summarize as "Found 10+ critical issues/suggestions/optional nits" and only output the first 10 items.
- Don't compress the blank lines between sections; keep them as-is for readability.
- If there is any issue requires code changes, append a brief follow-up question to ask whether the user wants to apply the fix(es) after the structured output. For example: "Would you like me to use the Suggested fix(es) to address these issues?"

### Template B (no issues)

```markdown
## Code Review Summary
? No issues found.
```
