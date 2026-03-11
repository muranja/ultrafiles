# SPDX-License-Identifier: GPL-3.0-or-later
"""Properties dialog for files and folders"""

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, Gio, GLib

from ..widgets.file_item import FileItem


def _format_permissions(mode: int) -> str:
    """Format Unix permissions as rwx string"""
    parts = []
    for who in ("Owner", "Group", "Other"):
        r = "r" if mode & 0o4 else "-"
        w = "w" if mode & 0o2 else "-"
        x = "x" if mode & 0o1 else "-"
        parts.append(f"{r}{w}{x}")
        mode >>= 3

    # Reverse because we process from least significant
    parts.reverse()
    return "  ".join(parts)


def _calculate_dir_size(path: str) -> str:
    """Calculate total size of a directory"""
    total = 0
    file_count = 0
    dir_count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            dir_count += len(dirnames)
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                    file_count += 1
                except OSError:
                    pass
    except OSError:
        pass

    size_str = GLib.format_size(total)
    return f"{size_str}  ({file_count} files, {dir_count} folders)"


def show_properties_dialog(parent_window, file_item: FileItem):
    """Show file/folder properties dialog.

    Args:
        parent_window: Parent window
        file_item: The FileItem to show properties for
    """
    dialog = Adw.Dialog()
    dialog.set_title("Properties")
    dialog.set_content_width(420)
    dialog.set_content_height(500)

    # Build content
    toolbar_view = Adw.ToolbarView()

    header = Adw.HeaderBar()
    toolbar_view.add_top_bar(header)

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    content.set_margin_start(16)
    content.set_margin_end(16)
    content.set_margin_top(12)
    content.set_margin_bottom(16)

    # Icon + Name header
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    header_box.set_halign(Gtk.Align.CENTER)
    header_box.set_margin_bottom(8)

    icon = Gtk.Image()
    icon.set_from_gicon(file_item.icon)
    icon.set_icon_size(Gtk.IconSize.LARGE)
    icon.set_pixel_size(64)
    header_box.append(icon)

    name_label = Gtk.Label(label=file_item.display_name)
    name_label.add_css_class("title-2")
    name_label.set_ellipsize(True)
    name_label.set_max_width_chars(30)
    header_box.append(name_label)

    content.append(header_box)

    # --- General Info ---
    general_group = Adw.PreferencesGroup()
    general_group.set_title("General")

    # Name
    _add_row(general_group, "Name", file_item.display_name)

    # Type
    _add_row(general_group, "Type", file_item.content_type_description)

    # MIME Type
    _add_row(general_group, "MIME Type", file_item.content_type)

    # Location
    parent_path = os.path.dirname(file_item.path)
    _add_row(general_group, "Location", parent_path)

    content.append(general_group)

    # --- Size ---
    size_group = Adw.PreferencesGroup()
    size_group.set_title("Size")

    if file_item.is_directory:
        # Calculate directory size in background
        size_row = _add_row(size_group, "Contents", "Calculating...")

        def calc_size():
            result = _calculate_dir_size(file_item.path)
            GLib.idle_add(lambda: size_row.set_subtitle(result) or False)

        import threading
        threading.Thread(target=calc_size, daemon=True).start()
    else:
        _add_row(size_group, "Size", file_item.size_formatted)
        # Also show exact bytes
        _add_row(size_group, "Exact", f"{file_item.size:,} bytes")

    content.append(size_group)

    # --- Timestamps ---
    time_group = Adw.PreferencesGroup()
    time_group.set_title("Timestamps")

    _add_row(time_group, "Modified", file_item.modified_formatted)

    # Try to get access and creation time
    try:
        stat = os.stat(file_item.path)
        import datetime

        atime = datetime.datetime.fromtimestamp(stat.st_atime)
        _add_row(time_group, "Accessed", atime.strftime("%Y-%m-%d %H:%M"))

        if hasattr(stat, "st_birthtime"):
            ctime = datetime.datetime.fromtimestamp(stat.st_birthtime)
            _add_row(time_group, "Created", ctime.strftime("%Y-%m-%d %H:%M"))
    except OSError:
        pass

    content.append(time_group)

    # --- Permissions ---
    try:
        stat = os.stat(file_item.path)
        perm_group = Adw.PreferencesGroup()
        perm_group.set_title("Permissions")

        mode = stat.st_mode
        _add_row(perm_group, "Permissions", _format_permissions(mode & 0o777))
        _add_row(perm_group, "Octal", f"{mode & 0o777:o}")
        _add_row(perm_group, "Owner UID", str(stat.st_uid))
        _add_row(perm_group, "Group GID", str(stat.st_gid))

        content.append(perm_group)
    except OSError:
        pass

    scrolled.set_child(content)
    toolbar_view.set_content(scrolled)
    dialog.set_child(toolbar_view)
    dialog.present(parent_window)


def _add_row(group: Adw.PreferencesGroup, title: str, value: str) -> Adw.ActionRow:
    """Add a read-only info row to a preferences group"""
    row = Adw.ActionRow()
    row.set_title(title)
    row.set_subtitle(value)
    row.set_subtitle_selectable(True)
    group.add(row)
    return row
