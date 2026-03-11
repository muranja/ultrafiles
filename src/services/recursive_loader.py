# SPDX-License-Identifier: GPL-3.0-or-later
"""Recursive Directory loader service — finds specific file types in subdirectories."""

import os
import mimetypes
import threading
import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GLib

from ..widgets.file_item import FileItem

# Ensure mimetypes DB is loaded
mimetypes.init()

class RecursiveLoader:
    """
    Loads files recursively from a directory using os.scandir() in a background thread.
    Filters files based on a predicate (e.g. is_media).
    """

    BATCH_SIZE = 50

    def __init__(self):
        self._cancellable = None
        self._callback = None
        self._root_file = None

    def load_recursive(self, root: Gio.File, callback, file_filter=None):
        """
        Start loading directory contents recursively.

        Args:
            root: The root directory to start scanning
            callback: Function called with (items, error)
            file_filter: Optional function(filename, path) -> bool. 
                         If None, includes all files.
        """
        # Cancel any pending operation
        if self._cancellable:
            self._cancellable.cancel()

        self._cancellable = Gio.Cancellable()
        self._callback = callback
        self._root_file = root
        self._filter = file_filter

        path = root.get_path()
        if path is None:
            # Recursive scan only supported for local files currently
            error = GLib.Error.new_literal(
                Gio.io_error_quark(), 
                "Recursive scan only supported for local files", 
                Gio.IOErrorEnum.NOT_SUPPORTED
            )
            callback(None, error)
            return

        # Launch scan in background thread
        cancellable = self._cancellable
        threading.Thread(
            target=self._scan_thread,
            args=(path, cancellable),
            daemon=True,
        ).start()

    def _scan_thread(self, root_path, cancellable):
        """Background thread: recursive scan."""
        try:
            batch = []
            stack = [root_path]

            while stack:
                if cancellable.is_cancelled():
                    return

                current_path = stack.pop()
                
                try:
                    # Sort of like os.walk but manual control
                    with os.scandir(current_path) as it:
                        for entry in it:
                            if cancellable.is_cancelled():
                                return

                            if entry.is_dir(follow_symlinks=False):
                                # Don't follow symlinks to avoid loops/mess
                                if not entry.name.startswith("."):
                                    stack.append(entry.path)
                            elif entry.is_file():
                                if not entry.name.startswith("."):
                                    # Check filter
                                    if self._should_include(entry):
                                        try:
                                            # We need a Gio.File for the parent of THIS file
                                            # FileItem expects (info, parent_gfile)
                                            # This is a bit inefficient if we create a GFile for every parent.
                                            # But FileItem uses parent.get_child(name).
                                            # Let's create parent GFile.
                                            parent_gfile = Gio.File.new_for_path(current_path)
                                            info = self._entry_to_fileinfo(entry)
                                            item = FileItem(info, parent_gfile)
                                            batch.append(item)
                                        except Exception:
                                            continue

                            if len(batch) >= self.BATCH_SIZE:
                                items = batch
                                batch = []
                                GLib.idle_add(self._deliver_batch, items, cancellable)
                except OSError:
                    continue

            # Deliver remaining
            if batch and not cancellable.is_cancelled():
                GLib.idle_add(self._deliver_batch, batch, cancellable)

            # Signal completion
            if not cancellable.is_cancelled():
                GLib.idle_add(self._deliver_complete, cancellable)

        except Exception as e:
            if not cancellable.is_cancelled():
                GLib.idle_add(self._deliver_error, str(e), cancellable)

    def _should_include(self, entry):
        """Check if file should be included."""
        try:
            # If no filter, include all
            if not self._filter:
                return True
                
            # Basic fast filter based on extension/mime
            # If filter is "media", check mime
            if self._filter == "media":
                ct, _ = mimetypes.guess_type(entry.name, strict=False)
                if ct and (ct.startswith("image/") or ct.startswith("video/") or ct.startswith("audio/")):
                    return True
                return False
                
            # Check callable
            if callable(self._filter):
                return self._filter(entry.name, entry.path)
                
            return True
        except Exception:
            return False

    @staticmethod
    def _entry_to_fileinfo(entry):
        """Convert os.DirEntry to Gio.FileInfo (simplified for recursive view)."""
        # Re-using logic from DirectoryLoader would be cleaner, but hard to import static method if not public
        # duplicating minimal logic for speed
        info = Gio.FileInfo()
        info.set_name(entry.name)
        info.set_display_name(entry.name)
        
        try:
            st = entry.stat()
            info.set_size(st.st_size)
            info.set_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED, int(st.st_mtime))
        except OSError:
            pass

        info.set_file_type(Gio.FileType.REGULAR)
        
        ct, _ = mimetypes.guess_type(entry.name, strict=False)
        content_type = ct or "application/octet-stream"
        
        info.set_attribute_string(Gio.FILE_ATTRIBUTE_STANDARD_FAST_CONTENT_TYPE, content_type)
        info.set_content_type(content_type)
        
        icon = Gio.content_type_get_icon(content_type)
        if icon:
            info.set_icon(icon)

        return info

    def _deliver_batch(self, items, cancellable):
        if not cancellable.is_cancelled() and self._callback:
            self._callback(items, None)
        return False

    def _deliver_complete(self, cancellable):
        if not cancellable.is_cancelled() and self._callback:
            self._callback(None, None)
        return False

    def _deliver_error(self, message, cancellable):
        if not cancellable.is_cancelled() and self._callback:
            error = GLib.Error.new_literal(
                Gio.io_error_quark(), message, Gio.IOErrorEnum.FAILED
            )
            self._callback(None, error)
        return False

    def cancel(self):
        if self._cancellable:
            self._cancellable.cancel()
            self._cancellable = None
