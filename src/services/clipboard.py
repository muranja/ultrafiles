# SPDX-License-Identifier: GPL-3.0-or-later
"""Clipboard service for file operations"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, Gio, GLib, GObject


class ClipboardOperation:
    """Enum for clipboard operation types"""

    COPY = 0
    CUT = 1


class ClipboardService(GObject.Object):
    """Service for managing file clipboard operations"""

    __gtype_name__ = "ClipboardService"

    __gsignals__ = {
        "clipboard-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self._files = []  # List of (GFile, is_directory)
        self._operation = None
        self._source_dir = None

    def copy(self, files, source_dir):
        """Set clipboard to copy files"""
        self._files = files
        self._operation = ClipboardOperation.COPY
        self._source_dir = source_dir
        self._update_system_clipboard()
        self.emit("clipboard-changed")

    def cut(self, files, source_dir):
        """Set clipboard to cut (move) files"""
        self._files = files
        self._operation = ClipboardOperation.CUT
        self._source_dir = source_dir
        self._update_system_clipboard()
        self.emit("clipboard-changed")

    def clear(self):
        """Clear the clipboard"""
        self._files = []
        self._operation = None
        self._source_dir = None
        self.emit("clipboard-changed")

    def has_files(self) -> bool:
        """Check if clipboard has files"""
        return len(self._files) > 0

    def get_files(self):
        """Get list of files in clipboard"""
        return self._files

    def get_operation(self):
        """Get the clipboard operation type"""
        return self._operation

    def get_source_dir(self):
        """Get the source directory"""
        return self._source_dir

    def is_cut(self) -> bool:
        """Check if operation is cut (move)"""
        return self._operation == ClipboardOperation.CUT

    def _update_system_clipboard(self):
        """Update system clipboard with file URIs"""
        display = Gdk.Display.get_default()
        if not display:
            return

        clipboard = display.get_clipboard()
        if not clipboard:
            return

        # Create file URIs list
        uris = []
        for f in self._files:
            if isinstance(f, tuple):
                gfile = f[0]
            else:
                gfile = f
            uris.append(gfile.get_uri())

        # Set clipboard content
        content = Gdk.ContentProvider.new_for_values(
            [Gdk.FileList.new(uris)],
            Gdk.Atom.intern_static_string("x-special/gnome-copied-files"),
        )
        clipboard.set_content(content)

    @staticmethod
    def from_system_clipboard() -> tuple:
        """Try to get files from system clipboard"""
        display = Gdk.Display.get_default()
        if not display:
            return None, None

        clipboard = display.get_clipboard()
        if not clipboard:
            return None, None

        # Try to read file list from clipboard
        # This is a simplified version - full implementation would use
        # clipboard.read_value() with Gdk.FileList
        return None, None


# Global clipboard service instance
_clipboard_service = None


def get_clipboard_service() -> ClipboardService:
    """Get the global clipboard service instance"""
    global _clipboard_service
    if _clipboard_service is None:
        _clipboard_service = ClipboardService()
    return _clipboard_service
