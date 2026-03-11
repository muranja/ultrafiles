# SPDX-License-Identifier: GPL-3.0-or-later
"""
Meme Remix Dialog - UI for cropping and audio mixing.
"""
import os
import threading
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from ..services.meme_editor_service import MemeEditorService


def show_remix_dialog(parent, file_item, on_complete_callback=None):
    """Helper to show the remix dialog."""
    if not file_item.is_video():
        return

    dialog = RemixDialog(file_item)
    dialog.set_transient_for(parent)
    if on_complete_callback:
        dialog._on_complete_callback = on_complete_callback
    dialog.present()


class RemixDialog(Adw.Window):
    __gtype_name__ = "MemeRemixDialog"

    def __init__(self, file_item):
        super().__init__(title="Remix Meme")
        self.set_modal(True)
        self.set_default_size(400, 300)

        self._file_item = file_item
        self._service = MemeEditorService()
        self._on_complete_callback = None

        self._build_ui()

    def _build_ui(self):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(content)

        # Header
        header = Adw.HeaderBar()
        content.append(header)

        # Main Layout
        page = Adw.PreferencesPage()
        content.append(page)

        # Section 1: Cropping
        crop_group = Adw.PreferencesGroup(title="Formatting")
        page.add(crop_group)

        crop_row = Adw.ActionRow(
            title="Crop to Vertical (9:16)",
            subtitle="Best for TikTok/Shorts/Reels",
        )
        crop_btn = Gtk.Button(label="Crop")
        crop_btn.set_valign(Gtk.Align.CENTER)
        crop_btn.add_css_class("suggested-action")
        crop_btn.connect("clicked", self._on_crop_clicked)
        crop_row.add_suffix(crop_btn)
        crop_group.add(crop_row)

        # Section 2: Audio Mixing (Placeholder UI for now)
        audio_group = Adw.PreferencesGroup(title="Audio")
        page.add(audio_group)

        audio_row = Adw.ActionRow(title="Add Sound Effect", subtitle="Overlay an audio file")
        audio_btn = Gtk.Button(label="Select Audio...")
        audio_btn.set_valign(Gtk.Align.CENTER)
        audio_btn.connect("clicked", self._on_audio_clicked)
        audio_row.add_suffix(audio_btn)
        audio_group.add(audio_row)

        # Progress Spinner (hidden by default)
        self._spinner = Gtk.Spinner()
        self._spinner.set_halign(Gtk.Align.CENTER)
        self._spinner.set_margin_top(16)
        content.append(self._spinner)

    def _set_processing_state(self, is_processing: bool):
        """Disables UI and shows a spinner while rendering."""
        self.get_content().set_sensitive(not is_processing)
        if is_processing:
            self._spinner.start()
        else:
            self._spinner.stop()

    def _on_crop_clicked(self, btn):
        self._set_processing_state(True)
        input_path = self._file_item.path
        filename = os.path.basename(input_path)
        output_name = f"vertical_{filename}"

        # Run in a background thread so the GTK UI doesn't freeze
        threading.Thread(
            target=self._run_crop_task,
            args=(input_path, output_name),
            daemon=True,
        ).start()

    def _run_crop_task(self, input_path, output_name):
        try:
            output_path = self._service.crop_to_vertical(input_path, output_name)
            GLib.idle_add(self._on_task_success, output_path)
        except Exception as e:
            GLib.idle_add(self._on_task_error, str(e))

    def _on_audio_clicked(self, btn):
        # TODO: Implement file chooser for audio track, then call self._service.add_sound_effect
        print("Audio mixing UI coming soon!")

    def _on_task_success(self, output_path):
        self._set_processing_state(False)
        print(f"Success! Saved to {output_path}")
        if self._on_complete_callback:
            self._on_complete_callback(output_path)
        self.close()

    def _on_task_error(self, error_msg):
        self._set_processing_state(False)
        print(f"Error processing meme: {error_msg}")
        # Could show an Adw.Toast or Error Dialog here
