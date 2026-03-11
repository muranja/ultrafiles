# SPDX-License-Identifier: GPL-3.0-or-later
"""
Meme Metadata Dialog - For Captions and Themes
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gio
from ..services.meme_metadata_service import MemeMetadataService
from ..services.tags_service import TagsService


def show_metadata_dialog(parent, file_path: str, on_save_callback=None):
    """Helper to show dialog"""
    dialog = MetadataDialog(file_path)
    dialog.set_transient_for(parent)
    if on_save_callback:
        dialog._on_save_callback = on_save_callback
    dialog.present()


class MetadataDialog(Adw.Window):
    """Dialog to edit Meme Captions and Themes"""

    __gtype_name__ = "MemeMetadataDialog"

    def __init__(self, file_path: str):
        super().__init__(title="Edit Meme Data")
        self.set_modal(True)
        self.set_default_size(450, 400)

        self._path = file_path
        self._uri = Gio.File.new_for_path(file_path).get_uri()
        self._meme_service = MemeMetadataService()
        self._tags_service = TagsService()
        self._on_save_callback = None

        self._build_ui()
        self._load_data()

    def _build_ui(self):
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

        # Form Container
        page = Adw.PreferencesPage()
        content.append(page)

        # Theme Group
        theme_group = Adw.PreferencesGroup(title="Meme Category")
        page.add(theme_group)

        self._theme_entry = Adw.EntryRow(title="Theme (e.g., Funny, Sad, Reaction)")
        theme_group.add(self._theme_entry)

        # Caption Group
        caption_group = Adw.PreferencesGroup(title="Searchable Caption / Transcript")
        page.add(caption_group)

        # Use a TextView for multiline captions instead of a single-line entry
        text_bg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        text_bg.add_css_class("card")
        text_bg.set_margin_start(12)
        text_bg.set_margin_end(12)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(150)
        self._caption_view = Gtk.TextView()
        self._caption_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._caption_view.set_margin_top(8)
        self._caption_view.set_margin_bottom(8)
        self._caption_view.set_margin_start(8)
        self._caption_view.set_margin_end(8)

        scrolled.set_child(self._caption_view)
        text_bg.append(scrolled)
        caption_group.add(text_bg)

    def _load_data(self):
        caption = self._meme_service.get_caption(self._uri)
        if caption:
            buffer = self._caption_view.get_buffer()
            buffer.set_text(caption)

        themes = self._tags_service.get_tags_for_file(self._uri)
        if themes:
            self._theme_entry.set_text(", ".join(themes))

    def _on_save(self, btn):
        theme_text = self._theme_entry.get_text()
        themes = [t.strip() for t in theme_text.split(",") if t.strip()]

        buffer = self._caption_view.get_buffer()
        start, end = buffer.get_bounds()
        caption = buffer.get_text(start, end, True)

        caption_ok = self._meme_service.set_caption(self._uri, caption)
        self._tags_service.set_tags_for_file(self._uri, themes)

        if self._on_save_callback:
            self._on_save_callback(caption_ok)

        self.close()
