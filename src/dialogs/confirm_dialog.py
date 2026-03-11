# SPDX-License-Identifier: GPL-3.0-or-later
"""Confirm dialog for destructive operations"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw


def show_confirm_dialog(
    parent_window,
    heading: str,
    body: str,
    confirm_label: str = "Delete",
    callback=None,
):
    """Show a confirmation dialog.

    Args:
        parent_window: Parent window
        heading: Dialog heading
        body: Dialog body text
        confirm_label: Label for the destructive action button
        callback: Called with (confirmed: bool)
    """
    dialog = Adw.AlertDialog()
    dialog.set_heading(heading)
    dialog.set_body(body)

    dialog.add_response("cancel", "Cancel")
    dialog.add_response("confirm", confirm_label)
    dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    def on_response(dlg, response):
        if callback:
            callback(response == "confirm")

    dialog.connect("response", on_response)
    dialog.present(parent_window)


def show_new_folder_dialog(parent_window, callback):
    """Show a dialog to create a new folder.

    Args:
        parent_window: Parent window
        callback: Called with (folder_name: str) on confirm, None on cancel
    """
    dialog = Adw.AlertDialog()
    dialog.set_heading("New Folder")
    dialog.set_body("Enter a name for the new folder")

    dialog.add_response("cancel", "Cancel")
    dialog.add_response("create", "Create")
    dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("create")
    dialog.set_close_response("cancel")

    entry = Adw.EntryRow()
    entry.set_title("Folder name")
    entry.set_text("New Folder")

    # Wrap in a list box for proper Adw styling
    listbox = Adw.PreferencesGroup()
    listbox.add(entry)

    dialog.set_extra_child(listbox)

    def on_text_changed(row):
        text = row.get_text().strip()
        is_valid = len(text) > 0 and "/" not in text
        dialog.set_response_enabled("create", is_valid)

    entry.connect("changed", on_text_changed)

    def on_response(dlg, response):
        if response == "create":
            callback(entry.get_text().strip())
        else:
            callback(None)

    dialog.connect("response", on_response)
    dialog.present(parent_window)
