---
name: gtk_development_rails
description: STRICT guardrails for UltraFiles development. Adhere to these usage patterns, widget choices, and styling rules.
---

# GTK4 & LibAdwaita Development Rails

> [!IMPORTANT]
> These are strict rules. Deviations require explicit user approval.

## 1. UI Patterns (The "Premium" Look)

- **Windowing**:
  - **MUST** use `Adw.ApplicationWindow` as the root.
  - **MUST** use `Adw.HeaderBar` for the top bar.
  - **MUST** set `application.style_manager.color_scheme = ADW_COLOR_SCHEME_PREFER_DARK` by default.
- **Empty States**:
  - **MUST** use `Adw.StatusPage` with an icon (from `Adwaita` strings) and title/description.
  - **NEVER** leave a view empty or blank.
- **Dialogs**:
  - **MUST** use `Adw.MessageDialog` for alerts/confirmations (NOT `Gtk.MessageDialog`).
  - **MUST** use `Adw.Window` or `Adw.PreferencesWindow` for custom dialogs.

## 2. Widget Selection Rails

| Function | REQUIRED Widget | BANNED Widget |
|----------|-----------------|---------------|
| Lists | `Gtk.ListView` / `Gtk.ColumnView` | `Gtk.ListBox` (for >50 items) |
| Grids | `Gtk.GridView` | `Gtk.FlowBox` (for >50 items) |
| Scrolling | `Gtk.ScrolledWindow` | - |
| Search | `Gtk.SearchEntry` | `Gtk.Entry` (for search) |
| Sidebars | `Adw.NavigationSplitView` | `Gtk.Paned` |

## 3. Async & I/O Rails

- **Main Thread**:
  - **NEVER** perform blocking I/O (file read, network, extensive calculation) on the main thread.
  - **MUST** use `Gio.File.xxx_async` methods or run in a thread/Task.
- **Image Loading**:
  - **MUST** use `GdkPixbuf.Pixbuf.new_from_file_at_scale_async` or background loading.
  - **NEVER** synchronize load images in list/grid cells.

## 4. Code Structure Rails

- **Typing**: **MUST** use type hints for all function arguments and return values.
- **Templates**: **SHOULD** use `.ui` templates for any widget with >3 children.
- **Signals**:
  - **MUST** disconnect signals in `do_map/do_unmap` or `dispose` if they connect to global objects.
  - **MUST** use weak references where cyclic references are possible.
