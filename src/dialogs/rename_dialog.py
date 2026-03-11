# SPDX-License-Identifier: GPL-3.0-or-later
"""Rename dialog - entry-based rename with validation"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, GLib


def show_rename_dialog(parent_window, current_name: str, callback):
    """Show a rename dialog.

    Args:
        parent_window: Parent Adw.ApplicationWindow
        current_name: Current file/folder name
        callback: Called with (new_name: str) on confirm, or None on cancel
    """
    dialog = Adw.AlertDialog()
    dialog.set_heading("Rename")
    dialog.set_body(f'Enter new name for "{current_name}"')

    dialog.add_response("cancel", "Cancel")
    dialog.add_response("rename", "Rename")
    dialog.set_response_appearance("rename", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("rename")
    dialog.set_close_response("cancel")

    # Add entry as extra child
    entry = Gtk.Entry()
    entry.set_text(current_name)
    entry.set_hexpand(True)
    entry.add_css_class("rename-entry")

    # Select just the filename part (not extension) for convenience
    if "." in current_name and not current_name.startswith("."):
        name_part = current_name.rsplit(".", 1)[0]
        GLib.idle_add(
            lambda: entry.select_region(0, len(name_part)) or False
        )
    else:
        GLib.idle_add(lambda: entry.select_region(0, -1) or False)

    # Validate input
    def on_text_changed(entry_widget):
        text = entry_widget.get_text().strip()
        is_valid = len(text) > 0 and "/" not in text and text != current_name
        dialog.set_response_enabled("rename", is_valid)

    entry.connect("changed", on_text_changed)

    # Enter key confirms
    def on_activate(entry_widget):
        text = entry_widget.get_text().strip()
        if text and "/" not in text and text != current_name:
            dialog.response("rename")

    entry.connect("activate", on_activate)

    dialog.set_extra_child(entry)

    # Initially disable rename if name unchanged
    dialog.set_response_enabled("rename", False)

    def on_response(dlg, response):
        if response == "rename":
            new_name = entry.get_text().strip()
            callback(new_name)
        else:
            callback(None)

    dialog.connect("response", on_response)
    dialog.present(parent_window)
