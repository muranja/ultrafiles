# SPDX-License-Identifier: GPL-3.0-or-later
"""
Metadata Dialog
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ..services.metadata_service import MetadataService

def show_metadata_dialog(parent, file_path: str, on_save_callback=None):
    """Helper to show dialog"""
    dialog = MetadataDialog(file_path)
    dialog.set_transient_for(parent)
    if on_save_callback:
        dialog._on_save_callback = on_save_callback
    dialog.present()

class MetadataDialog(Adw.Window):
    """Dialog to edit metadata"""
    __gtype_name__ = "MetadataDialog"

    def __init__(self, file_path: str):
        super().__init__(title="Edit Metadata")
        self.set_modal(True)
        self.set_default_size(400, 500)
        
        self._path = file_path
        self._service = MetadataService()
        self._on_save_callback = None
        
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # Initial setup
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(content)
        
        # Header
        header = Adw.HeaderBar()
        content.append(header)
        
        # Save button
        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)
        
        # Form
        group = Adw.PreferencesGroup()
        page = Adw.PreferencesPage()
        page.add(group)
        content.append(page)
        
        self._entries = {}
        
        fields = [
            ("Title", "title"),
            ("Artist", "artist"),
            ("Album", "album"),
            ("Year", "year"),
            ("Genre", "genre"),
            ("Track Number", "track")
        ]
        
        for label_text, key in fields:
            row = Adw.EntryRow(title=label_text)
            group.add(row)
            self._entries[key] = row

    def _load_data(self):
        tags = self._service.read_metadata(self._path)
        for key, row in self._entries.items():
            if key in tags:
                row.set_text(tags[key])

    def _on_save(self, btn):
        tags = {}
        for key, row in self._entries.items():
            tags[key] = row.get_text()
            
        success = self._service.write_metadata(self._path, tags)
        
        if self._on_save_callback:
            self._on_save_callback(success)
            
        self.close()
