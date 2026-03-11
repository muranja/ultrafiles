# SPDX-License-Identifier: GPL-3.0-or-later
"""Directory loader service — uses os.scandir() for fast enumeration."""

import os
import stat
import mimetypes
import threading

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GLib

from ..widgets.file_item import FileItem


# Ensure mimetypes DB is loaded once
mimetypes.init()


class DirectoryLoader:
    """Loads directory contents using os.scandir() in a background thread.

    Much faster than Gio.File.enumerate_children_async because it avoids
    per-file GIO attribute marshalling overhead.
    """

    # Attributes string kept for compatibility (used by search path)
    ATTRIBUTES = ",".join(
        [
            Gio.FILE_ATTRIBUTE_STANDARD_NAME,
            Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME,
            Gio.FILE_ATTRIBUTE_STANDARD_TYPE,
            Gio.FILE_ATTRIBUTE_STANDARD_SIZE,
            Gio.FILE_ATTRIBUTE_STANDARD_ICON,
            Gio.FILE_ATTRIBUTE_STANDARD_FAST_CONTENT_TYPE,
            Gio.FILE_ATTRIBUTE_STANDARD_IS_HIDDEN,
            Gio.FILE_ATTRIBUTE_STANDARD_IS_SYMLINK,
            Gio.FILE_ATTRIBUTE_TIME_MODIFIED,
        ]
    )

    BATCH_SIZE = 200

    def __init__(self):
        self._cancellable = None
        self._callback = None
        self._parent_file = None

    def load_directory(self, directory: Gio.File, callback):
        """
        Start loading directory contents.

        Args:
            directory: The directory to enumerate
            callback: Function called with (items, error) —
                      items is list of FileItem or None when complete,
                      error is GLib.Error or None
        """
        # Cancel any pending operation
        if self._cancellable:
            self._cancellable.cancel()

        self._cancellable = Gio.Cancellable()
        self._callback = callback
        self._parent_file = directory

        path = directory.get_path()
        if path is None:
            # Non-local URI — fall back to GIO async enumeration
            self._load_gio_async(directory)
            return

        # Launch os.scandir in a background thread
        cancellable = self._cancellable
        threading.Thread(
            target=self._scan_thread,
            args=(path, directory, cancellable),
            daemon=True,
        ).start()

    def _scan_thread(self, dirpath, parent_gfile, cancellable):
        """Background thread: enumerate with os.scandir, build FileInfo, deliver batches."""
        try:
            batch = []
            for entry in os.scandir(dirpath):
                if cancellable.is_cancelled():
                    return

                try:
                    info = self._entry_to_fileinfo(entry)
                    item = FileItem(info, parent_gfile)
                    batch.append(item)
                except Exception:
                    continue

                if len(batch) >= self.BATCH_SIZE:
                    items = batch
                    batch = []
                    GLib.idle_add(self._deliver_batch, items, cancellable)

            # Deliver remaining items
            if batch and not cancellable.is_cancelled():
                GLib.idle_add(self._deliver_batch, batch, cancellable)

            # Signal completion
            if not cancellable.is_cancelled():
                GLib.idle_add(self._deliver_complete, cancellable)

        except OSError as e:
            if not cancellable.is_cancelled():
                GLib.idle_add(self._deliver_error, str(e), cancellable)

    @staticmethod
    def _entry_to_fileinfo(entry):
        """Convert an os.DirEntry to a Gio.FileInfo."""
        info = Gio.FileInfo()
        name = entry.name

        info.set_name(name)
        info.set_display_name(name)

        # Symlink check (no extra syscall — cached by DirEntry)
        is_symlink = entry.is_symlink()
        info.set_is_symlink(is_symlink)

        # Stat (cached by DirEntry for non-symlinks, follow_symlinks=True)
        try:
            st = entry.stat(follow_symlinks=True)
        except OSError:
            st = entry.stat(follow_symlinks=False)

        is_dir = stat.S_ISDIR(st.st_mode)

        # File type
        if is_dir:
            info.set_file_type(Gio.FileType.DIRECTORY)
        elif is_symlink:
            info.set_file_type(Gio.FileType.SYMBOLIC_LINK)
        else:
            info.set_file_type(Gio.FileType.REGULAR)

        # Size
        info.set_size(st.st_size)

        # Modification time
        info.set_attribute_uint64(
            Gio.FILE_ATTRIBUTE_TIME_MODIFIED, int(st.st_mtime)
        )

        # Hidden
        info.set_attribute_boolean(
            Gio.FILE_ATTRIBUTE_STANDARD_IS_HIDDEN, name.startswith(".")
        )

        # Content type (extension-based — instant)
        if is_dir:
            content_type = "inode/directory"
        else:
            ct, _ = mimetypes.guess_type(name, strict=False)
            content_type = ct or "application/octet-stream"

        info.set_attribute_string(
            Gio.FILE_ATTRIBUTE_STANDARD_FAST_CONTENT_TYPE, content_type
        )
        # Also set content_type so get_content_type() works
        info.set_content_type(content_type)

        # Icon from content type
        icon = Gio.content_type_get_icon(content_type)
        if icon:
            info.set_icon(icon)

        return info

    def _deliver_batch(self, items, cancellable):
        """Main-thread callback: deliver a batch of items."""
        if not cancellable.is_cancelled() and self._callback:
            self._callback(items, None)
        return False  # Don't repeat

    def _deliver_complete(self, cancellable):
        """Main-thread callback: signal loading complete."""
        if not cancellable.is_cancelled() and self._callback:
            self._callback(None, None)
        return False

    def _deliver_error(self, message, cancellable):
        """Main-thread callback: deliver error."""
        if not cancellable.is_cancelled() and self._callback:
            error = GLib.Error.new_literal(
                Gio.io_error_quark(), message, Gio.IOErrorEnum.FAILED
            )
            self._callback(None, error)
        return False

    # ── Fallback: GIO async for non-local URIs ──

    def _load_gio_async(self, directory):
        """Fallback for non-local (e.g. network) directories."""
        directory.enumerate_children_async(
            self.ATTRIBUTES,
            Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
            GLib.PRIORITY_DEFAULT,
            self._cancellable,
            self._on_enumerate_ready,
            None,
        )

    def _on_enumerate_ready(self, directory, result, user_data):
        try:
            self._enumerator = directory.enumerate_children_finish(result)
            self._load_next_batch()
        except GLib.Error as e:
            if e.code != Gio.IOErrorEnum.CANCELLED:
                self._callback(None, e)

    def _load_next_batch(self):
        self._enumerator.next_files_async(
            self.BATCH_SIZE,
            GLib.PRIORITY_DEFAULT,
            self._cancellable,
            self._on_files_ready,
            None,
        )

    def _on_files_ready(self, enumerator, result, user_data):
        try:
            file_infos = enumerator.next_files_finish(result)
            if file_infos:
                items = []
                for fi in file_infos:
                    try:
                        items.append(FileItem(fi, self._parent_file))
                    except Exception:
                        pass
                self._callback(items, None)
                self._load_next_batch()
            else:
                enumerator.close_async(
                    GLib.PRIORITY_DEFAULT, None, lambda e, r, d: None, None
                )
                self._callback(None, None)
        except GLib.Error as e:
            if e.code != Gio.IOErrorEnum.CANCELLED:
                self._callback(None, e)

    def cancel(self):
        """Cancel any pending operation."""
        if self._cancellable:
            self._cancellable.cancel()
            self._cancellable = None
