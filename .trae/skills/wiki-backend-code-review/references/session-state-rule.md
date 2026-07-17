# Rule Catalog - Session State & Cache Consistency

## Scope
- Covers: Cache invalidation before reads, session state synchronization across processes, cookie/authentication state management, stale cache prevention, cross-process state propagation.
- Does NOT cover: SSE streaming (sse-streaming-rule.md), filesystem/vault ops (filesystem-vault-rule.md), or general security (security-rule.md).

## Rules

### Cache invalidation before JSON reads

IsUrgent: True
Category: Session State & Cache Consistency

### Description

When reading shared state files (JSON config, cookie store, session data) that are written by external processes (subprocesses, child processes, background schedulers), always invalidate the in-memory cache before reading. The 30-second TTL cache in the parent process will return stale data written by the child process.

### Suggested Fix

Before calling \_read_json()\ or any method that reads from a shared file:
1. Call \store.invalidate_cache()\ to clear the in-memory cache.
2. Then call \store._read_json()\ to get fresh data.

Example:
\\\python
store = get_cookie_store()
store.invalidate_cache()  # Must clear cache before reading
data = store._read_json()
\\\

### Cross-process state propagation

IsUrgent: True
Category: Session State & Cache Consistency

### Description

When a subprocess writes shared state (e.g., browser login subprocess writes \cookies.json\), the parent process must be notified or must proactively read fresh data. Parent process in-memory cache will NOT be updated by child process writes.

### Suggested Fix

After subprocess writes shared state:
1. Subprocess should write to a well-known file path.
2. Parent process must call \invalidate_cache()\ before reading the file.
3. Parent process should propagate state to running services (e.g., inject cookies into worker browser).

### Stale session state detection

IsUrgent: True
Category: Session State & Cache Consistency

### Description

When checking session/login state, do NOT only check for the existence of cookie names. Also verify:
1. Cookie values match the latest known-good values from the persistent store.
2. Cookie expiration dates are still valid.
3. Identity cookies (unb, cookie2, sgcookie) have not been replaced with stale values from a previous login.

### Suggested Fix

Implement a three-tier check for session validity:
1. **Missing**: Are required cookie names present?
2. **Expired**: Do any cookies have \expires < now\?
3. **Stale**: Do cookie values match the latest values in the persistent store (JSON)?

All three tiers must pass for the session to be considered valid.

### Runtime cookie injection after state writes

IsUrgent: True
Category: Session State & Cache Consistency

### Description

After writing updated session state (cookies, tokens) to the persistent store, the running browser worker context must also be updated. Writing to JSON/SQLite alone is insufficient—the in-memory browser context still holds old cookies.

### Suggested Fix

After any cookie/token write operation:
1. Write to persistent store (JSON/SQLite).
2. Call \sync_cookie_layers_from_json()\ to update layer states.
3. Call \inject_cookie_store_to_worker_browser()\ to push new cookies into the running browser context.
4. Force token refresh if identity cookies changed.

### Layer state synchronization after writes

IsUrgent: True
Category: Session State & Cache Consistency

### Description

When cookies are written via \export_cookies()\, the in-memory layer states (identity/session/tracking) in \CookieRotator\ are NOT automatically updated. This causes \/cookies/layers\ to show stale invalid states even after successful login.

### Suggested Fix

After \export_cookies()\ succeeds:
1. Call \sync_cookie_layers_from_json()\ to read fresh JSON and update layer states.
2. Or call \orch.cookie_rotator.sync_state_from_cookies(cookie_map)\ with the new cookie values.

### Cache staleness in health checks

IsUrgent: False
Category: Session State & Cache Consistency

### Description

Health check endpoints (\/health\, \/cookies/layers\, \/me\) that read shared state files must always invalidate the cache before reading. These endpoints are polled frequently by the frontend and must reflect the latest state.

### Suggested Fix

Add \store.invalidate_cache()\ at the start of any health check or status endpoint that reads shared state files.
