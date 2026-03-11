# SPDX-License-Identifier: GPL-3.0-or-later
"""
File Operations Service
Handles async file manipulation (Copy, Move, Trash, Delete).
Adheres to strict async rails (no blocking I/O).
"""

import gi
from typing import List, Callable, Optional
import os

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib, GObject

class FileOperationsService(GObject.Object):
    """
    Service for performing asynchronous file operations.
    Signals:
        operation-progress: (current_file_name, current_bytes, total_bytes)
        operation-complete: (success, error_message)
    """
    
    __gsignals__ = {
        'operation-progress': (GObject.SignalFlags.RUN_FIRST, None, (str, int, int)),
        'operation-complete': (GObject.SignalFlags.RUN_FIRST, None, (bool, str)),
    }

    def __init__(self):
        super().__init__()
        self._cancellable = Gio.Cancellable()

    def trash_files(self, files: List[Gio.File], callback: Optional[Callable] = None):
        """
        Move files to trash asynchronously.
        
        Args:
            files: List of Gio.File objects to trash
            callback: Optional function to call when done (success, error)
        """
        if not files:
            if callback: callback(True, None)
            return

        # Process one by one (could be parallelized, but sequential is safer for now)
        self._trash_next(list(files), callback)

    def _trash_next(self, remaining_files: List[Gio.File], callback: Optional[Callable]):
        if not remaining_files:
            self.emit('operation-complete', True, "")
            if callback: callback(True, None)
            return

        file = remaining_files.pop(0)
        
        def on_trash_finish(source, result, user_data):
            try:
                source.trash_finish(result)
                # Proceed to next
                self._trash_next(remaining_files, callback)
            except GLib.Error as e:
                # Stop on error? or continue? For now, report error and stop.
                self.emit('operation-complete', False, e.message)
                if callback: callback(False, e.message)

        file.trash_async(GLib.PRIORITY_DEFAULT, self._cancellable, on_trash_finish, None)

    def copy_file(self, source: Gio.File, destination: Gio.File, callback: Optional[Callable] = None):
        """
        Copy a single file asynchronously.
        """
        def on_copy_progress(current, total, user_data):
            self.emit('operation-progress', source.get_basename(), current, total)

        def on_copy_finish(source, result, user_data):
            try:
                source.copy_finish(result)
                self.emit('operation-complete', True, "")
                if callback: callback(True, None)
            except GLib.Error as e:
                self.emit('operation-complete', False, e.message)
                if callback: callback(False, e.message)

        source.copy_async(
            destination,
            Gio.FileCopyFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            self._cancellable,
            on_copy_progress,
            None,
            on_copy_finish,
            None
        )

    def move_file(self, source: Gio.File, destination: Gio.File, callback: Optional[Callable] = None):
        """
        Move a single file asynchronously.
        """
        def on_move_progress(current, total, user_data):
            self.emit('operation-progress', source.get_basename(), current, total)

        def on_move_finish(source, result, user_data):
            try:
                source.move_finish(result)
                self.emit('operation-complete', True, "")
                if callback: callback(True, None)
            except GLib.Error as e:
                self.emit('operation-complete', False, e.message)
                if callback: callback(False, e.message)

        source.move_async(
            destination,
            Gio.FileCopyFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            self._cancellable,
            on_move_progress,
            None,
            on_move_finish,
            None
        )

    def delete_file(self, file: Gio.File, callback: Optional[Callable] = None):
        """
        Permanently delete a file asynchronously.
        """
        def on_delete_finish(source, result, user_data):
            try:
                source.delete_finish(result)
                self.emit('operation-complete', True, "")
                if callback: callback(True, None)
            except GLib.Error as e:
                self.emit('operation-complete', False, e.message)
                if callback: callback(False, e.message)

        file.delete_async(GLib.PRIORITY_DEFAULT, self._cancellable, on_delete_finish, None)

    def cancel(self):
        """Cancel current operation."""
        self._cancellable.cancel()
        self._cancellable = Gio.Cancellable() # Reset
