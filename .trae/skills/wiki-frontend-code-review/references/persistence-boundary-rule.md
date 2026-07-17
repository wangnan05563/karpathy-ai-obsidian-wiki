# Rule Catalog - Persistence and Storage Boundary

## Scope
- Covers: cross-origin data persistence, browser storage as cache fallback, sensitive data storage, single source of truth, data migration from old storage.
- Does NOT cover: Vue composition API patterns (vue-composition-rule.md), Pinia store patterns (pinia-store-rule.md), config form state (config-state-rule.md).

## Rules

### PB-1: Cross-origin data must use backend persistence

IsUrgent: True
Category: Persistence and Storage Boundary

### Description

Browser storage (localStorage / IndexedDB / sessionStorage) is isolated per origin (protocol + domain + port). Data shared across origins (e.g., dev mode localhost:5173 vs prod mode localhost:3000) must use backend persistence as the authoritative source. Browser storage serves only as a per-origin cache fallback.

### Suggested Fix

Use backend API as authoritative source. Browser storage as cache with fallback:

```typescript
async function loadData() {
  try {
    const res = await fetch('/api/data');
    if (res.ok) return await res.json();
  } catch {
    // backend unavailable, fallback to cache
  }
  return await dbGetAll(STORE);
}
```

### PB-2: Sensitive data must not be stored in localStorage as plaintext

IsUrgent: True
Category: Persistence and Storage Boundary

### Description

API keys, tokens, and credentials must not be stored in localStorage as plaintext (XSS risk + dual-track inconsistency). Backend config.json is the sole authoritative source. Frontend stores only masked values for display.

### Suggested Fix

Store only masked values in frontend state. Send plaintext to backend on save:

```typescript
// Wrong: localStorage.setItem('apiKey', plainKey)
// Right:
async function saveApiKey(key: string) {
  await fetch('/api/ai/config', {
    method: 'PUT',
    body: JSON.stringify({ apiKey: key }),
  });
  apiKeyMasked.value = maskKey(key); // only masked value in memory
}
```

### PB-3: Single source of truth for each data category

IsUrgent: True
Category: Persistence and Storage Boundary

### Description

Each data category (config / session / user preference) must have exactly one authoritative source. Other storage layers serve as cache and must be fallback-capable. Dual-track writing (e.g., apiKey in both localStorage and config.json) causes state inconsistency.

### Suggested Fix

Identify authoritative source per data category in config. Cache layers must be fallback-only and clearly marked.

### PB-4: Cache write failure must not block main flow

IsUrgent: True
Category: Persistence and Storage Boundary

### Description

IndexedDB / localStorage write failures (e.g., private mode) must not block the main flow. Log warning and continue. Cache is optimization, not requirement.

### Suggested Fix

Wrap cache writes in try/catch with warning log:

```typescript
try {
  await dbPut(STORE, record);
} catch (err) {
  console.warn('Cache write failed, non-blocking:', err);
}
```

### PB-5: Backend unavailable must have fallback path

IsUrgent: True
Category: Persistence and Storage Boundary

### Description

Backend API call failures must fall back to local cache. Main flow must not block. Fallback must log warning for debugging.

### Suggested Fix

```typescript
async function loadConversations() {
  try {
    const res = await fetch('/api/conversations');
    if (res.ok) {
      const data = await res.json();
      return data.conversations;
    }
  } catch (err) {
    console.warn('Backend unavailable, falling back to cache:', err);
  }
  return await dbGetAll(STORE);
}
```

### PB-6: Historical dual-track data must be migrated

IsUrgent: False
Category: Persistence and Storage Boundary

### Description

When discovering historical dual-track data (e.g., old apiKey in localStorage), provide a one-time migration function. Must be idempotent (re-running produces no duplicates).

### Suggested Fix

```typescript
async function migrateLegacyData() {
  const legacy = localStorage.getItem('apiKey:deepseek');
  if (legacy) {
    await fetch('/api/ai/config', {
      method: 'PUT',
      body: JSON.stringify({ apiKey: legacy }),
    });
    localStorage.removeItem('apiKey:deepseek');
  }
}
```

## Checklist
- [ ] Cross-origin data uses backend as authoritative source
- [ ] Sensitive data not stored in localStorage as plaintext
- [ ] Each data category has single authoritative source
- [ ] Cache write failures do not block main flow
- [ ] Backend unavailable has fallback path with warning log
- [ ] Historical dual-track data has idempotent migration