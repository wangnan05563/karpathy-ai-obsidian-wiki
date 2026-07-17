# Rule Catalog - Display Field Mapping & Normalization

## Scope
- Covers: Display field rendering, brand/region/seller alignment, field metadata consistency, stale data display prevention, frontend-backend field mapping.
- Does NOT cover: SSE streaming, vis-network rendering, or general Vue Composition API patterns.

## Rules

### Display fields must use normalized data from backend

IsUrgent: True
Category: Display Field Mapping & Normalization

### Description

Frontend components rendering display fields (brand, region, seller_nick, publish_time) must trust the backend-normalized data. The backend normalize_display_fields() function corrects field misalignment (e.g., seller_nick actually being region, region actually being seller nick). Frontend should not attempt its own field correction logic.

### Suggested Fix

- Use corrected_display from backend API responses directly
- Do not implement duplicate field validation/correction in frontend
- If backend returns normalized field_map, use it for dynamic column rendering

### Brand field must respect backend normalization

IsUrgent: True
Category: Display Field Mapping & Normalization

### Description

The brand field in task_links.display is a redundant display field derived from search API, title inference, or detail page collection. The backend validates brand against the current item title and clears stale brands that do not match. Frontend must display the brand value as-is from the backend without attempting to re-infer or validate.

### Suggested Fix

- Render brand from payload.brand or display.brand directly
- Do not implement brand inference logic in frontend
- Show empty/placeholder when brand is empty string
- Do not attempt to extract brand from title in frontend

### Field metadata must drive column rendering

IsUrgent: False
Category: Display Field Mapping & Normalization

### Description

When rendering dynamic columns (brand, region, seller_nick, etc.), use the field_map provided by the backend normalize_display_fields() function to determine which columns to show and how to render them. This ensures frontend display matches backend data availability.

### Suggested Fix

- Use field_map from backend to drive column visibility
- Map field types to renderers (text, seller, tag, datetime, etc.)
- Do not hardcode column definitions when field_map is available

### Stale display values must not be cached in frontend state

IsUrgent: True
Category: Display Field Mapping & Normalization

### Description

When display data is refreshed (e.g., after detail page collection or official collection), stale display values in frontend state (cached lists, filtered results) must be invalidated. Showing stale brand/region/seller data after a refresh causes user confusion.

### Suggested Fix

- Invalidate filtered results after refresh operations
- Re-fetch list data after detail/official collection completes
- Do not rely on client-side filtering for stale data after mutations
- Use ref-based filter state to ensure consistent API parameters across calls

### Region/seller misalignment detection must be backend-only

IsUrgent: True
Category: Display Field Mapping & Normalization

### Description

The region and seller_nick fields in search API responses have unstable semantics - region may contain seller nick and vice versa. This misalignment is corrected by backend normalize_display_fields(). Frontend must not attempt to detect or correct this misalignment.

### Suggested Fix

- Trust backend-corrected seller_nick and region values
- Do not implement region detection logic in frontend
- Do not swap seller_nick/region based on frontend heuristics
- Display masked nicknames (e.g., 芯***鱼) as-is from backend

### Filter state must be centralized for all API calls

IsUrgent: True
Category: Display Field Mapping & Normalization

### Description

When multiple API calls share the same filter criteria (keyword, region, brand), use a single source of truth (e.g., useRef/filtersRef.current) to pass parameters. This prevents filter drift between list and distribution/statistics endpoints.

### Suggested Fix

- Centralize filter state in a ref (filtersRef.current)
- All API calls read from the same ref
- Update ref when any filter changes
- Document which filters apply to which endpoints

### Dynamic brand filter options must come from current data

IsUrgent: False
Category: Display Field Mapping & Normalization

### Description

Brand filter dropdown options should be derived from the currently loaded data (payload.brand or display.brand), not hardcoded or cached from previous loads. This ensures filter options reflect the actual data available.

### Suggested Fix

- Derive brandOptions from current items list
- Update brandOptions when list data changes
- Clear brandFilter when list data is replaced (e.g., after task switch)
