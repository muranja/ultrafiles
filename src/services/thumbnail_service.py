# SPDX-License-Identifier: GPL-3.0-or-later
"""
Thumbnail Service
Generates thumbnails using GnomeDesktop.DesktopThumbnailFactory.
Adheres to strict async rails (threading for blocking factory calls).
"""

import gi
import threading
from typing import Optional

gi.require_version("GObject", "2.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GnomeDesktop", "4.0")

from gi.repository import GObject, GLib, GnomeDesktop, GdkPixbuf, Gio

class ThumbnailService(GObject.Object):
    """
    Service for generating thumbnails.
    signals:
        thumbnail-ready: (uri, path)
    """
    
    __gsignals__ = {
        'thumbnail-ready': (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
    }

    def __init__(self):
        super().__init__()
        self._factory = GnomeDesktop.DesktopThumbnailFactory.new(
            GnomeDesktop.DesktopThumbnailSize.LARGE
        )
        self._queue = []
        self._queued_uris: set[str] = set()  # deduplication
        self._processing = False
        self._lock = threading.Lock()

    def request_thumbnail(self, item):
        """
        Request thumbnail generation for FileItem.
        item: FileItem
        """
        if not item.uri or not item.modified_time:
            return

        with self._lock:
            # Skip if already queued or processing
            if item.uri in self._queued_uris:
                return
            self._queued_uris.add(item.uri)
            self._queue.append((item.uri, item.modified_time, item.content_type))
            if not self._processing:
                self._processing = True
                threading.Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self):
        """Process queue in a thread"""
        while True:
            item_data = None
            with self._lock:
                if self._queue:
                    item_data = self._queue.pop(0)
                else:
                    self._processing = False
                    return
            
            if item_data:
                uri, mtime, mime_type = item_data
                self._generate_one(uri, mtime, mime_type)

    def _generate_one(self, uri, mtime, mime_type):
        """Generate one thumbnail"""
        try:
            # Lookup first just in case
            path = self._factory.lookup(uri, mtime)
            if path:
                GLib.idle_add(self.emit, 'thumbnail-ready', uri, path)
                return

            if not self._factory.can_thumbnail(uri, mime_type, mtime):
                return
                
            # Generate
            # Note: generate_thumbnail is blocking and might be slow for video
            pixbuf = self._factory.generate_thumbnail(uri, mime_type)
            if pixbuf:
                self._factory.save_thumbnail(pixbuf, uri, mtime)
                # Lookup again to get path
                path = self._factory.lookup(uri, mtime)
                if path:
                    GLib.idle_add(self.emit, 'thumbnail-ready', uri, path)
                else:
                    # Failed to save?
                    pass
            else:
                 # Failed to generate
                 # Create failed thumbnail to avoid retry loop
                 self._factory.create_failed_thumbnail(uri, mtime)
                 
        except Exception as e:
            print(f"Thumbnail error for {uri}: {e}")
            # Mark failed
            try:
                self._factory.create_failed_thumbnail(uri, mtime)
            except:
                pass

    def cancel_pending(self):
        """Cancel all pending thumbnail requests (e.g. on directory change)"""
        with self._lock:
            self._queue.clear()
            self._queued_uris.clear()
