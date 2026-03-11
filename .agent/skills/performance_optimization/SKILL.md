---
name: performance_rails
description: Performance requirements and optimization patterns that MUST be followed.
---

# Performance Rails

## 1. List/Grid View Rails

- **Recycling**:
  - **MUST** use `Gtk.SignalListItemFactory`.
  - **setup**: Create widgets ONLY. No data binding.
  - **bind**: Set data from item. Keep lightweight.
  - **unbind**: Clear references/images to free memory.
- **Model**:
  - **MUST** use `Gtk.FilterListModel` for search filtering (native C performance).
  - **AVOID** Python-side filtering for lists > 1000 items.

## 2. Search Rails

- **Engine**:
  - **MUST** check for `ripgrep` binary availability.
  - **FALLBACK** to `git grep` or `find` if `rg` is missing.
  - **NEVER** implement recursive python `os.walk` search for content.
- **Threading**:
  - **MUST** run search process in non-blocking subprocess.
  - **MUST** read output in chunks (not line-by-line event spam) to update UI.

## 3. Media Rails

- **Thumbnails**:
  - **MUST** cancel thumbnail generation if the item scrolls out of view.
  - **MUST** use a disk cache (XDG standard) to avoid regeneration.
- **Memory**:
  - `Gtk.Video` / Pipelines **MUST** be set to NULL state when hidden.
