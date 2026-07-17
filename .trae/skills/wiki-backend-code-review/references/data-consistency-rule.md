# Rule Catalog - Data Consistency & Display Normalization

## Scope
- Covers: Display field normalization, brand inference validation, cross-table data consistency, stale display value cleanup, enrichment pipeline correctness.
- Does NOT cover: SSE streaming, filesystem/vault ops, or general security.

## Rules

### Display field normalization must validate brand against current title

IsUrgent: True
Category: Data Consistency & Display Normalization

### Description

When enriching or displaying brand values from task_links.display or search API results, the brand must be validated against the current item title. If the title is available and the brand does not match the title (or any known brand alias present in the title), the brand must be cleared rather than retained from stale historical values.

Brand is a redundant display field stored in task_links.display. It may originate from search API, title inference, or historical legacy values. When the current title is available, the brand must be explainable by the title or title aliases; otherwise it should be re-inferred or cleared.

### Suggested Fix

Implement a validation function that:
1. Receives brand, title, and seller_candidate
2. If brand exists AND (no title OR brand matches title) -> return brand
3. If seller_candidate matches title -> return seller_candidate
4. Infer brand from title using known brand aliases
5. Return empty string if no match found

### Raw brand from API must pass title validation

IsUrgent: True
Category: Data Consistency & Display Normalization

### Description

When extracting brand from raw API response (search API, detail page), the brand must be validated against the item title before being returned. A raw brand value that does not match the title (or any known brand alias in the title) should be discarded rather than propagated.

### Suggested Fix

In extract_brand() or equivalent, after finding a raw brand value:
1. Strip whitespace from raw_brand
2. Check if title is empty OR raw_brand matches title via _brand_candidate_matches_title
3. Only return raw_brand if validation passes
4. Fall through to seller_candidate/title inference if validation fails

### Detail page collection must overwrite stale display brand

IsUrgent: True
Category: Data Consistency & Display Normalization

### Description

When refreshing item details via detail page scraping (both /api/items/{id}/refresh and official collection /api/evaluations/{id}/collect-official), the resulting display data must write back the detail page brand value - even if empty. An empty detail.brand means the detail page could not identify a brand, which is a valid result that should clear stale display.brand values from search API or historical inference.

Previously, the merge logic only overwrote display.brand when detail.brand was non-empty, causing stale brands to persist indefinitely.

### Suggested Fix

Extract a unified display merge helper that:
1. Merges non-brand fields with non-empty-only overwrite policy
2. Always writes detail.brand to display (empty or not)
3. Persists merged display to task_links via upsert_task_link

### Evaluation enrichment must normalize link display before extraction

IsUrgent: True
Category: Data Consistency & Display Normalization

### Description

When enriching evaluation payloads with item data from task_links.display (via _enrich_eval_with_item), the display data must be normalized through normalize_display_fields() before brand/title/region fields are extracted. Historical display JSON may contain misaligned fields (e.g., brand from wrong search run) that should be corrected before enrichment.

### Suggested Fix

In _enrich_eval_with_item(), before extracting brand/region/seller fields from link:
1. If link data exists, call normalize_display_fields(link)
2. Use the corrected display for subsequent field extraction
3. This ensures stale brands are cleaned before being injected into evaluation payloads

### Worker detail phase must not fallback to search summary brand

IsUrgent: False
Category: Data Consistency & Display Normalization

### Description

In the worker pipeline, when updating task_links.display after collecting detail page data, the brand should use only the detail page brand. Previously, the code used detail.brand or summary.brand, which caused detail page empty brands to fall back to search summary brands - reintroducing stale brands that the detail page explicitly did not identify.

### Suggested Fix

Change brand assignment from detail.brand or summary.brand to only detail.brand

### Official collection must sync task_links.display after evaluation

IsUrgent: True
Category: Data Consistency & Display Normalization

### Description

The official collection flow (_collect_official_and_evaluate) updates items table and evaluation events, but previously did NOT sync task_links.display. This means even after a successful official collection, the display brand remained stale and would continue to be shown in evaluation detail pages.

### Suggested Fix

After persisting items and sellers tables, call sync_item_display_from_detail() to update task_links.display with the detail page brand value. This ensures evaluation enrichment reads the correct brand.

### Cross-table display consistency must be verified

IsUrgent: False
Category: Data Consistency & Display Normalization

### Description

When multiple data sources contribute to the same display (search API -> task_links.display, detail page -> task_links.display, official collection -> task_links.display), verify that:
1. All write paths use the same merge logic
2. All read paths normalize display before extraction
3. No write path falls back to stale values when a newer path produces empty

### Suggested Fix

Add a review checklist item:
- All display write paths use consistent merge logic
- All display read paths call normalize_display_fields before extraction
- Empty values from newer sources are NOT overridden by older stale values
