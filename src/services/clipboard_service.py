# SPDX-License-Identifier: GPL-3.0-or-later
"""
Clipboard Service
Handles Copy/Cut operations and integrates with the system clipboard.
Adheres to strict typing and async rails.
"""

import gi
from typing import List, Optional, Tuple
from enum import Enum, auto

gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gdk, Gio, GObject

class ClipboardAction(Enum):
    COPY = auto()
    CUT = auto()

class ClipboardService(GObject.Object):
    """
    Manages file clipboard operations.
    Signals:
        changed: Emitted when clipboard content changes.
    """
    
    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, display: Gdk.Display = None):
        super().__init__()
        self._action: ClipboardAction = ClipboardAction.COPY
        self._files: List[Gio.File] = []
        
        # Get default display if not provided
        if display is None:
            display = Gdk.Display.get_default()
        
        self._clipboard = display.get_clipboard()
        # We could connect to system clipboard changes here if needed
        # self._clipboard.connect("changed", self._on_system_clipboard_changed)

    def set_files(self, files: List[Gio.File], action: ClipboardAction = ClipboardAction.COPY) -> None:
        """
        Set files to the internal clipboard and update system clipboard.
        
        Args:
            files: List of Gio.File objects
            action: COPY or CUT
        """
        self._files = files
        self._action = action
        
        # Format for system clipboard (text/uri-list)
        if files:
            uris = [f.get_uri() for f in files]
            uri_list = "\r\n".join(uris)
            
            # Set to system clipboard
            content = Gdk.ContentProvider.new_for_bytes("text/uri-list", GObject.Bytes.new(uri_list.encode("utf-8")))
            self._clipboard.set_content(content)
        else:
            self._clipboard.set_content(None)
            
        self.emit('changed')

    def get_files(self) -> Tuple[List[Gio.File], ClipboardAction]:
        """
        Get current files from internal clipboard.
        
        Returns:
            Tuple of (List[Gio.File], ClipboardAction)
        """
        # TODO: In the future, we should also check the system clipboard
        # if the internal list is empty, to support pasting from other file managers.
        return self._files, self._action

    def clear(self) -> None:
        """Clear the clipboard."""
        self.set_files([], ClipboardAction.COPY)

    @property
    def has_content(self) -> bool:
        """Check if clipboard has content."""
        return len(self._files) > 0
