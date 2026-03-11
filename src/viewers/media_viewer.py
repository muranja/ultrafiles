# SPDX-License-Identifier: GPL-3.0-or-later
"""Media Viewer Widget for UltraFiles — handles images, video, and audio."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GdkPixbuf, GObject

from ..widgets.file_item import FileItem


class MediaViewer(Gtk.Box):
    """Full-screen media viewer for images, video, and audio files."""

    __gsignals__ = {
        "close-viewer": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, items: list[FileItem], start_index: int):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("media-viewer-content")

        self._items = items
        self._current_index = start_index
        self._rotation = 0
        self._preloaded: dict[int, Gdk.Texture] = {}  # index → texture cache
        self._media_file = None  # current video MediaFile

        self.set_vexpand(True)
        self.set_hexpand(True)

        self._build_ui()
        self._load_current_item()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        """Build the viewer UI."""
        # ── Header toolbar ──
        self._header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._header.add_css_class("toolbar")
        self.append(self._header)

        back_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        back_btn.set_tooltip_text("Back to Files (Esc)")
        back_btn.connect("clicked", lambda b: self.emit("close-viewer"))
        self._header.append(back_btn)

        self._title_label = Gtk.Label()
        self._title_label.add_css_class("title")
        self._title_label.set_hexpand(True)
        self._title_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self._title_label.set_max_width_chars(60)
        self._header.append(self._title_label)

        # Rotation buttons (only shown for images)
        self._rotate_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._rotate_box.add_css_class("linked")

        rotate_left = Gtk.Button.new_from_icon_name("object-rotate-left-symbolic")
        rotate_left.set_tooltip_text("Rotate Left")
        rotate_left.connect("clicked", lambda b: self._rotate(-90))
        self._rotate_box.append(rotate_left)

        rotate_right = Gtk.Button.new_from_icon_name("object-rotate-right-symbolic")
        rotate_right.set_tooltip_text("Rotate Right")
        rotate_right.connect("clicked", lambda b: self._rotate(90))
        self._rotate_box.append(rotate_right)

        self._header.append(self._rotate_box)

        # Open externally button
        open_btn = Gtk.Button.new_from_icon_name("external-link-symbolic")
        open_btn.set_tooltip_text("Open in External App")
        open_btn.connect("clicked", self._on_open_external)
        self._header.append(open_btn)

        # ── Content stack ──
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(150)
        self._stack.set_vexpand(True)
        self._stack.set_hexpand(True)
        self.append(self._stack)

        # Image view
        self._image = Gtk.Picture()
        self._image.set_can_shrink(True)
        self._image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._stack.add_named(self._image, "image")

        # Video player — Gtk.Picture scales video properly via content_fit
        video_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        video_box.set_vexpand(True)
        video_box.set_hexpand(True)

        self._video_picture = Gtk.Picture()
        self._video_picture.set_can_shrink(True)
        self._video_picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._video_picture.set_vexpand(True)
        self._video_picture.set_hexpand(True)

        # Overlay for play-button centre icon
        self._video_overlay = Gtk.Overlay()
        self._video_overlay.set_child(self._video_picture)
        self._video_overlay.set_vexpand(True)

        # Play/pause click handler on the picture area
        click = Gtk.GestureClick()
        click.connect("released", self._on_video_clicked)
        self._video_overlay.add_controller(click)

        video_box.append(self._video_overlay)

        # Playback controls bar
        self._video_controls = Gtk.MediaControls()
        video_box.append(self._video_controls)

        self._stack.add_named(video_box, "video")

        # Audio view — icon + video controls
        audio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        audio_box.set_valign(Gtk.Align.CENTER)
        audio_box.set_halign(Gtk.Align.CENTER)

        audio_icon = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        audio_icon.set_pixel_size(96)
        audio_icon.add_css_class("audio-icon")
        audio_box.append(audio_icon)

        self._audio_title = Gtk.Label()
        self._audio_title.add_css_class("title-2")
        self._audio_title.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self._audio_title.set_max_width_chars(50)
        audio_box.append(self._audio_title)

        # Embed a Gtk.Video for audio controls (play/pause/seek)
        self._audio_video = Gtk.Video()
        self._audio_video.set_autoplay(True)
        self._audio_video.set_size_request(420, 50)
        audio_box.append(self._audio_video)

        self._stack.add_named(audio_box, "audio")

        # Unsupported / error page
        self._error_page = Adw.StatusPage()
        self._error_page.set_icon_name("dialog-warning-symbolic")
        self._error_page.set_title("Cannot Preview")
        self._error_page.set_description("This file type is not supported for preview.")

        open_ext_btn = Gtk.Button(label="Open with Default App")
        open_ext_btn.add_css_class("suggested-action")
        open_ext_btn.set_halign(Gtk.Align.CENTER)
        open_ext_btn.connect("clicked", self._on_open_external)
        self._error_page.set_child(open_ext_btn)

        self._stack.add_named(self._error_page, "unsupported")

        # ── Bottom navigation bar ──
        action_bar = Gtk.ActionBar()
        self.append(action_bar)

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self._prev_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self._prev_btn.set_tooltip_text("Previous (←)")
        self._prev_btn.connect("clicked", self._on_prev)
        nav_box.append(self._prev_btn)

        self._info_label = Gtk.Label()
        nav_box.append(self._info_label)

        self._next_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self._next_btn.set_tooltip_text("Next (→)")
        self._next_btn.connect("clicked", self._on_next)
        nav_box.append(self._next_btn)

        action_bar.set_center_widget(nav_box)

        # ── Keyboard navigation ──
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    # ── Loading ──────────────────────────────────────────────────────

    def _get_current_item(self) -> FileItem | None:
        if not self._items or self._current_index < 0 or self._current_index >= len(self._items):
            return None
        return self._items[self._current_index]

    def _load_current_item(self):
        """Load the current media item."""
        item = self._get_current_item()
        if not item:
            return

        self._title_label.set_label(item.display_name)
        self._info_label.set_label(f"{self._current_index + 1} / {len(self._items)}")
        self._rotation = 0

        # Update nav buttons
        self._prev_btn.set_sensitive(self._current_index > 0)
        self._next_btn.set_sensitive(self._current_index < len(self._items) - 1)

        # Show rotation controls only for images
        self._rotate_box.set_visible(item.is_image())

        # Stop any active playback before loading new content
        self._stop_playback()

        if item.is_image():
            self._load_image(item)
        elif item.is_video():
            self._load_video(item)
        elif item.is_audio():
            self._load_audio(item)
        else:
            self._stack.set_visible_child_name("unsupported")

        # Preload adjacent images for instant navigation
        self._preload_adjacent()

    def _load_image(self, item: FileItem):
        """Load an image file."""
        idx = self._current_index

        # Use preloaded texture if available
        if idx in self._preloaded:
            self._image.set_paintable(self._preloaded[idx])
            self._stack.set_visible_child_name("image")
            return

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(item.path)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self._preloaded[idx] = texture
            self._image.set_paintable(texture)
            self._stack.set_visible_child_name("image")
        except Exception:
            # Fallback: let GTK try loading directly
            self._image.set_filename(item.path)
            self._stack.set_visible_child_name("image")

    def _load_video(self, item: FileItem):
        """Load a video file using Gtk.Picture + Gtk.MediaFile."""
        mf = Gtk.MediaFile.new_for_file(item.gfile)
        self._media_file = mf
        self._video_picture.set_paintable(mf)
        self._video_controls.set_media_stream(mf)
        mf.set_muted(False)
        mf.play()
        self._stack.set_visible_child_name("video")

        # Watch for errors
        mf.connect("notify::error", self._on_stream_error)

    def _load_audio(self, item: FileItem):
        """Load an audio file — show icon + playback controls."""
        self._audio_title.set_label(item.display_name)
        self._audio_video.set_file(item.gfile)
        self._stack.set_visible_child_name("audio")

        stream = self._audio_video.get_media_stream()
        if stream:
            stream.connect("notify::error", self._on_stream_error)

    def _preload_adjacent(self):
        """Preload textures for the previous and next images."""
        for offset in (-1, 1):
            idx = self._current_index + offset
            if idx < 0 or idx >= len(self._items) or idx in self._preloaded:
                continue
            adj_item = self._items[idx]
            if adj_item.is_image():
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(adj_item.path)
                    self._preloaded[idx] = Gdk.Texture.new_for_pixbuf(pixbuf)
                except Exception:
                    pass

        # Evict textures far from current position to limit memory
        keep = {self._current_index - 1, self._current_index, self._current_index + 1}
        for k in list(self._preloaded.keys()):
            if k not in keep:
                del self._preloaded[k]

    # ── Playback control ─────────────────────────────────────────────

    def _stop_playback(self):
        """Stop all active media playback."""
        # Stop main video
        if self._media_file:
            self._media_file.set_playing(False)
            self._media_file = None
        self._video_picture.set_paintable(None)
        self._video_controls.set_media_stream(None)

        # Stop audio
        audio_stream = self._audio_video.get_media_stream()
        if audio_stream:
            audio_stream.set_playing(False)
        self._audio_video.set_file(None)

    def cleanup(self):
        """Release all resources. Call when closing the viewer."""
        self._stop_playback()
        self._preloaded.clear()

    # ── Signal handlers ──────────────────────────────────────────────

    def _on_video_clicked(self, gesture, n_press, x, y):
        """Toggle play/pause when the video area is clicked."""
        if self._media_file:
            self._media_file.set_playing(not self._media_file.get_playing())

    def _on_stream_error(self, stream, pspec):
        """Handle media stream error by showing the unsupported page."""
        error = stream.get_error()
        if error:
            self._error_page.set_description(f"Playback error: {error.message}")
            self._stack.set_visible_child_name("unsupported")

    def _on_open_external(self, *args):
        """Open current file with the default system application."""
        item = self._get_current_item()
        if item:
            try:
                Gio.AppInfo.launch_default_for_uri(item.uri, None)
            except Exception:
                pass

    # ── Rotation ─────────────────────────────────────────────────────

    def _rotate(self, degrees: int):
        """Rotate the current image."""
        item = self._get_current_item()
        if not item or not item.is_image():
            return

        self._rotation = (self._rotation + degrees) % 360
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(item.path)
            angle = self._rotation
            if angle == 90:
                pixbuf = pixbuf.rotate_simple(GdkPixbuf.PixbufRotation.CLOCKWISE)
            elif angle == 180:
                pixbuf = pixbuf.rotate_simple(GdkPixbuf.PixbufRotation.UPSIDEDOWN)
            elif angle == 270:
                pixbuf = pixbuf.rotate_simple(GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE)

            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self._image.set_paintable(texture)
            # Update cache with rotated version
            self._preloaded[self._current_index] = texture
        except Exception:
            pass

    # ── Navigation ───────────────────────────────────────────────────

    def _on_prev(self, *args):
        if self._current_index > 0:
            self._current_index -= 1
            self._load_current_item()

    def _on_next(self, *args):
        if self._current_index < len(self._items) - 1:
            self._current_index += 1
            self._load_current_item()

    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        if keyval == Gdk.KEY_Left:
            self._on_prev()
            return True
        elif keyval == Gdk.KEY_Right:
            self._on_next()
            return True
        elif keyval == Gdk.KEY_Escape:
            self.emit("close-viewer")
            return True
        return False

