# Rule Catalog - Configuration and State Management

## Scope
- Covers: config form state management, preset application, API key handling, save-before-update patterns, desensitized value roundtrip prevention.
- Does NOT cover: Vue composition API patterns (vue-composition-rule.md), Pinia store patterns (pinia-store-rule.md), or Element Plus component usage (element-plus-rule.md).

## Rules

### Save-before-update pattern for config forms

IsUrgent: True
Category: Configuration and State Management

### Description

When applying presets or configuration changes in Vue config forms, the component must await backend save success before updating local reactive state. Optimistic updates that diverge from backend state cause data loss.

### Suggested Fix

Use pessimistic update: await api.save(patch) first, then set local state from the saved response. Never set local state before awaiting the save.

### Desensitized value roundtrip prevention

IsUrgent: True
Category: Configuration and State Management

### Description

API keys returned from backend as masked values (e.g., ****xxxx) must not be sent back as real values during save. Track a separate rawValue state for submission, only updating it when the user actively types in the input field.

### Suggested Fix

Maintain two state variables: rawValue for submission and displayValue for rendering. On mount, set both from initial data. On user input, update only rawValue. On save, send rawValue. If rawValue starts with ****, skip sending it.

### Config model consistency

IsUrgent: False
Category: Configuration and State Management

### Description

Frontend config interfaces must match backend config models field-for-field. Mismatched field names or types cause silent data loss during save.

### Suggested Fix

Generate TypeScript interfaces from backend Pydantic models, or maintain a manual mapping table with assertions in tests.

### Feature toggle visual feedback

IsUrgent: False
Category: Configuration and State Management

### Description

When a feature toggle disables a section of the UI, the disabled section must show a clear visual indicator (opacity change, overlay message) so users understand why the controls are inactive.

### Suggested Fix

Apply opacity: 0.5 and pointerEvents: none to disabled sections, with an overlay message explaining the disabled state.
