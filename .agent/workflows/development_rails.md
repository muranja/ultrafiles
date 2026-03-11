---
description: Workflow to audit code against strict Development Rails
---

# Development Rails Audit Workflow

> [!IMPORTANT]
> Run this audit before marking ANY task as complete.

## 1. GTK Layout Check

- [ ] Root is `Adw.ApplicationWindow`?
- [ ] Dialogs are `Adw.MessageDialog` or `Adw.Window`?
- [ ] No `Gtk.ListBox` used for potentially large lists? (Use `Gtk.ListView`)

## 2. Async Safety Check

- [ ] No potentially blocking I/O on main thread?
- [ ] `Gio.File` operations use `_async` variants?
- [ ] Image loading is async?

## 3. Testing Check

- [ ] Unit tests exist in `tests/unit/`?
- [ ] External dependencies (`Gio`, `subprocess`) are mocked?
- [ ] Async tests use `GLib.MainLoop` properly?

## 4. Media Safety (If applicable)

- [ ] Metadata writes use temp files?
- [ ] Preview widgets perform cleanup on unmap?
