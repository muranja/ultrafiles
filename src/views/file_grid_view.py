# SPDX-License-Identifier: GPL-3.0-or-later
"""File grid view (icon/thumbnail view)"""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GLib, GObject, Gdk, Pango

from ..widgets.file_item import FileItem
from ..services.sorting import NaturalSorter


class FileGridView(Gtk.Box):
    """Grid view for files with thumbnails"""

    __gtype_name__ = "UltraFilesGridView"

    __gsignals__ = {
        "file-activated": (GObject.SignalFlags.RUN_FIRST, None, (FileItem,)),
        "rename-requested": (GObject.SignalFlags.RUN_FIRST, None, (FileItem, str)),
        "context-menu-requested": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (float, float, object),
        ),
    }

    # Zoom levels: (css_class, icon_size, thumb_size, cell_size)
    ZOOM_LEVELS = [
        ("zoom-small",  32,  48,  80),
        ("zoom-normal", 64,  80, 100),
        ("zoom-large",  96, 128, 150),
        ("zoom-xlarge", 128, 180, 210),
    ]

    def __init__(self, store: Gio.ListStore):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("file-grid-view")

        self._store = store
        self._settings = Gio.Settings.new("com.ultrafiles.UltraFiles")
        self._thumbnail_service = None
        self._tags_service = None
        self._zoom_index = 1  # default: "zoom-normal"

        self._build_ui()
        self._apply_zoom()
        
    def set_thumbnail_service(self, service):
        self._thumbnail_service = service
        
    def set_tags_service(self, service):
        self._tags_service = service

    def _build_ui(self):
        """Build the grid view UI"""
        # Cache sort settings to avoid GSettings lookups in comparator
        self._cache_sort_settings()

        self._filter_tag = None
        self._group_by = None  # None, "folder", "tag"

        # Create filter model
        self._filter = Gtk.CustomFilter.new(self._filter_func, None)
        self._filter_model = Gtk.FilterListModel.new(self._store, self._filter)

        # Create sorter
        self._sorter = Gtk.CustomSorter.new(self._compare_files, None)
        self._sort_model = Gtk.SortListModel.new(self._filter_model, self._sorter)
        self._sort_model.set_incremental(True)  # non-blocking sort

        # Selection model
        self._selection = Gtk.MultiSelection.new(self._sort_model)

        # Factory for grid items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_setup)
        factory.connect("bind", self._on_bind)
        factory.connect("unbind", self._on_unbind)

        # Create GridView
        self._grid_view = Gtk.GridView.new(self._selection, factory)
        self._grid_view.set_enable_rubberband(True)
        self._grid_view.set_single_click_activate(False)
        self._grid_view.set_min_columns(2)
        self._grid_view.set_max_columns(20)
        self._grid_view.connect("activate", self._on_activate)

        # Right-click for context menu
        right_click = Gtk.GestureClick()
        right_click.set_button(3)
        right_click.connect("pressed", self._on_right_click)
        self._grid_view.add_controller(right_click)



        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._grid_view)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        self.append(scrolled)

    def _on_setup(self, factory, list_item):
        """Create widget structure for grid items"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("file-grid-item")
        box.set_halign(Gtk.Align.CENTER)
        box.set_size_request(100, 100)

        # Overlay for badges
        overlay = Gtk.Overlay()
        overlay.set_halign(Gtk.Align.CENTER)

        # Thumbnail/icon container
        thumbnail_frame = Gtk.Frame()
        thumbnail_frame.add_css_class("thumbnail")
        
        # Stack for icon/thumbnail/video preview
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # Icon
        icon = Gtk.Image()
        icon.set_pixel_size(64)
        stack.add_named(icon, "icon")

        # Thumbnail image
        thumbnail = Gtk.Picture()
        thumbnail.set_size_request(80, 80)
        thumbnail.set_content_fit(Gtk.ContentFit.COVER)
        stack.add_named(thumbnail, "thumbnail")

        # Video preview (MediaFile)
        video_picture = Gtk.Picture()
        video_picture.set_size_request(80, 80)
        video_picture.set_content_fit(Gtk.ContentFit.COVER)
        stack.add_named(video_picture, "video")

        thumbnail_frame.set_child(stack)
        overlay.set_child(thumbnail_frame)
        
        # Git Badge
        git_badge = Gtk.Label()
        git_badge.add_css_class("git-badge")
        git_badge.set_halign(Gtk.Align.END)
        git_badge.set_valign(Gtk.Align.START)
        overlay.add_overlay(git_badge)
        
        # Tags Box
        tags_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        tags_box.set_halign(Gtk.Align.START)
        tags_box.set_valign(Gtk.Align.START)
        tags_box.set_margin_top(4)
        tags_box.set_margin_start(4)
        overlay.add_overlay(tags_box)
        
        box.append(overlay)

        # Filename label
        label = Gtk.EditableLabel()
        label.set_text("")
        label.add_css_class("filename")
        # EditableLabel configuration
        # label.set_width_chars(14)
        label.connect("notify::editing", self._on_editing_changed)
        
        box.append(label)
        
        # Store references
        box.stack = stack
        box.file_item = None
        box.media_file = None
        box.label_widget = label

        # Hover controller for video preview
        motion = Gtk.EventControllerMotion()
        motion.connect("enter", self._on_item_hover_enter)
        motion.connect("leave", self._on_item_hover_leave)
        motion.connect("motion", self._on_item_motion)
        box.add_controller(motion)

        list_item.set_child(box)

    def _on_bind(self, factory, list_item):
        """Bind file data to widgets"""
        box = list_item.get_child()
        item = list_item.get_item()

        # Get widgets
        overlay = box.get_first_child()
        label = overlay.get_next_sibling()
        
        # Get overlay children (Frame and Badge)
        # Assuming Frame is first child (set_child) or we check type
        child = overlay.get_first_child()
        thumbnail_frame = None
        git_badge = None
        tags_box = None
        
        while child:
            if isinstance(child, Gtk.Frame):
                thumbnail_frame = child
            elif isinstance(child, Gtk.Label):
                git_badge = child
            elif isinstance(child, Gtk.Box):
                tags_box = child
            child = child.get_next_sibling()
            
        stack = thumbnail_frame.get_child()
        icon = stack.get_child_by_name("icon")
        thumbnail = stack.get_child_by_name("thumbnail")

        # Set icon
        icon.set_from_gicon(item.icon)
        label.set_text(item.display_name)
        # Store original name for validation check
        box.original_name = item.display_name
        
        # Bind git status
        status = item.git_status
        if git_badge:
            git_badge.set_label("")
            git_badge.remove_css_class("git-modified")
            git_badge.remove_css_class("git-untracked")
            git_badge.remove_css_class("git-ignored")
            
            if status:
                if status == "modified":
                    git_badge.set_label("M")
                    git_badge.add_css_class("git-modified")
                elif status == "untracked":
                    git_badge.set_label("?")
                    git_badge.add_css_class("git-untracked")
                elif status == "ignored":
                    git_badge.set_label("!")
                    git_badge.add_css_class("git-ignored")
                elif status == "staged":
                    git_badge.set_label("A")
                    git_badge.add_css_class("git-staged")
                elif status == "conflict":
                    git_badge.set_label("C")
                    git_badge.add_css_class("git-conflict")

        # Check for thumbnail
        if item.thumbnail_path:
            try:
                thumbnail.set_filename(item.thumbnail_path)
                stack.set_visible_child_name("thumbnail")
            except Exception:
                stack.set_visible_child_name("icon")
        else:
            stack.set_visible_child_name("icon")
            # Request thumbnail
            if self._thumbnail_service:
                self._thumbnail_service.request_thumbnail(item)

        # Populate tags
        if tags_box:
            # Clear existing
            while True:
                child = tags_box.get_first_child()
                if not child: break
                tags_box.remove(child)
            
            if item.tags:
                for tag in item.tags:
                    dot = Gtk.Box()
                    dot.set_size_request(8, 8)
                    dot.add_css_class("tag-dot")
                    
                    # Set color
                    color = "#ffffff"
                    if self._tags_service:
                        color = self._tags_service.get_tag_color(tag)
                    
                    # CSS provider for color
                    provider = Gtk.CssProvider()
                    css = f"box {{ background-color: {color}; border-radius: 50%; }}"
                    provider.load_from_data(css.encode())
                    context = dot.get_style_context()
                    context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                    
                    tags_box.append(dot)

        # Store reference
        box.file_item = item
        box.media_file = None  # For video preview

    def _on_unbind(self, factory, list_item):
        """Unbind data (cleanup)"""
        box = list_item.get_child()
        if hasattr(box, "file_item"):
            # Stop any video preview
            if hasattr(box, "media_file") and box.media_file:
                box.media_file.clear()
            del box.file_item

    def _on_activate(self, grid_view, position):
        """Handle item activation (double-click/enter)"""
        item = self._selection.get_item(position)
        if item:
            self.emit("file-activated", item)

    def _on_right_click(self, gesture, n_press, x, y):
        """Handle right-click for context menu"""
        # Get selected item
        item = self._get_item_at_position(x, y)
        
        # Translate coordinates from grid view to wrapper box
        # x, y are relative to self._grid_view
        res = self._grid_view.translate_coordinates(self, x, y)
        if res:
            tx, ty = res
            self.emit("context-menu-requested", tx, ty, item)

    def _on_editing_changed(self, label, param):
        if not label.get_editing():
            # Editing finished
            new_name = label.get_text().strip()
            
            # Find parent box to get item
            # We need to traverse up from label
            # label -> box
            box = label.get_parent()
            if not hasattr(box, "file_item") or not box.file_item:
                return
                
            original = getattr(box, "original_name", box.file_item.display_name)
            
            if new_name and new_name != original:
                self.emit("rename-requested", box.file_item, new_name)
            else:
                # Revert if empty or unchanged
                label.set_text(original)

    def _on_item_hover_enter(self, controller, x, y):
        """Handle hover enter for video preview"""
        if not self._settings.get_boolean("video-preview-on-hover"):
            return

        box = controller.get_widget()
        if not hasattr(box, "file_item") or not box.file_item:
            return
            
        if box.file_item.is_video():
            self._start_preview(box)

    def _on_item_motion(self, controller, x, y):
        """Handle mouse motion for video scrubbing"""
        box = controller.get_widget()
        if not hasattr(box, "media_file") or not box.media_file:
            return

        media = box.media_file
        duration = media.get_duration() # microseconds
        if duration <= 0:
            return
            
        width = box.get_width()
        if width <= 0:
            return
            
        # Scrubbing
        # "stops when the cursor is above it" -> Pause while scrubbing
        if media.get_playing():
            media.set_playing(False)
            
        target_ts = int((x / width) * duration)
        target_ts = max(0, min(target_ts, duration))
        media.seek(target_ts)

    def _on_item_hover_leave(self, controller):
        """Handle hover leave - mute video preview but keep playing (sticky)"""
        box = controller.get_widget()
        if hasattr(box, "media_file") and box.media_file:
            box.media_file.set_muted(True)
            # Resume playback if we were scrubbing (paused)
            if not box.media_file.get_playing():
                 box.media_file.set_playing(True)
        
    def _start_preview(self, box):
        """Start video preview"""
        # Stop any existing preview on other items
        if hasattr(self, "_current_preview_box") and self._current_preview_box and self._current_preview_box != box:
             self._stop_preview(self._current_preview_box)
             
        self._current_preview_box = box

        if box.media_file:
            # Already loaded, just ensure unmuted and playing
            box.media_file.set_muted(False)
            box.media_file.set_playing(True)
            return
            
        try:
            media_file = Gtk.MediaFile.new_for_file(box.file_item.gfile)
            box.media_file = media_file
            
            # Get video picture widget
            video_picture = box.stack.get_child_by_name("video")
            video_picture.set_paintable(media_file)
            
            media_file.set_muted(False)
            media_file.play()
            box.stack.set_visible_child_name("video")
        except Exception as e:
            print(f"Preview error: {e}")

    def _stop_preview(self, box):
        """Stop video preview completely"""
        if hasattr(box, "media_file") and box.media_file:
            box.media_file.set_playing(False)
            box.media_file = None
            
        # Restore view
        if hasattr(box, "file_item") and box.file_item:
            if box.file_item.thumbnail_path:
                box.stack.set_visible_child_name("thumbnail")
            else:
                box.stack.set_visible_child_name("icon")
                
        if hasattr(self, "_current_preview_box") and self._current_preview_box == box:
            self._current_preview_box = None

    def _get_item_at_position(self, x, y):
        """Get file item at given coordinates"""
        for i in range(self._selection.get_n_items()):
            if self._selection.is_selected(i):
                return self._selection.get_item(i)
        return None

    def set_group_by(self, mode: str):
        """Set grouping mode ("folder", "tag", or None)"""
        if self._group_by != mode:
            self._group_by = mode
            self.refresh_sort()

    def set_filter_by_tag(self, tag_name: str):
        """Filter files by tag name (None to show all)"""
        if self._filter_tag != tag_name:
            self._filter_tag = tag_name
            self._filter.changed(Gtk.FilterChange.DIFFERENT)

    def _filter_func(self, item, user_data):
        """Filter function"""
        if not self._filter_tag:
            return True
        return self._filter_tag in (item.tags or [])

    def _cache_sort_settings(self):
        """Cache sort settings to avoid GSettings lookups in comparator"""
        self._cached_folders_first = self._settings.get_boolean("folders-first")
        self._cached_sort_by = self._settings.get_string("sort-by")
        self._cached_ascending = self._settings.get_boolean("sort-ascending")

    def _compare_files(self, item_a, item_b, user_data):
        """Compare function for sorting files (uses cached settings)"""
        # Grouping overrides standard sort
        if self._group_by == "folder":
            # Sort by parent folder name
            ret = NaturalSorter.compare(item_a, item_b, lambda x: x.parent_name)
            if ret != 0:
                return ret
        elif self._group_by == "tag":
            # Sort by first tag (naive)
            tags_a = item_a.tags or []
            tags_b = item_b.tags or []
            tag_a = tags_a[0] if tags_a else "zzzz" # Put untagged last
            tag_b = tags_b[0] if tags_b else "zzzz"
            if tag_a != tag_b:
                return -1 if tag_a < tag_b else 1

        if self._cached_folders_first:
            if item_a.is_directory and not item_b.is_directory:
                return -1
            if item_b.is_directory and not item_a.is_directory:
                return 1

        sort_by = self._cached_sort_by
        cmp_val = 0
        if sort_by == "name":
            cmp_val = NaturalSorter.compare(item_a, item_b, lambda x: x.display_name)
        elif sort_by == "size":
            cmp_val = (item_a.size > item_b.size) - (item_a.size < item_b.size)
        elif sort_by == "modified":
            cmp_val = (item_a.modified_time > item_b.modified_time) - (item_a.modified_time < item_b.modified_time)
        elif sort_by == "type":
            cmp_val = NaturalSorter.compare(item_a, item_b, lambda x: x.content_type)

        return cmp_val if self._cached_ascending else -cmp_val

    def select_all(self):
        """Select all items"""
        self._selection.select_all()

    def get_selected_items(self) -> list:
        """Get list of selected FileItems"""
        items = []
        # PyGObject makes GtkBitset iterable
        try:
             for pos in bitset:
                 item = self._selection.get_item(pos)
                 if item:
                     items.append(item)
        except TypeError:
             # Fallback if not iterable
             iter_obj = Gtk.BitsetIter()
             valid, pos = iter_obj.init_first(bitset)
             while valid:
                 item = self._selection.get_item(pos)
                 if item:
                     items.append(item)
                 valid, pos = iter_obj.next()
        return items

    def refresh_sort(self):
        """Refresh the sort order"""
        self._cache_sort_settings()
        self._sorter.changed(Gtk.SorterChange.DIFFERENT)

    # ── Zoom ──

    def _apply_zoom(self):
        """Apply the current zoom level via CSS class."""
        # Remove old zoom classes
        for css_cls, _, _, _ in self.ZOOM_LEVELS:
            self.remove_css_class(css_cls)

        css_cls, icon_px, thumb_px, cell_px = self.ZOOM_LEVELS[self._zoom_index]
        self.add_css_class(css_cls)

        # Apply dynamic sizes via a CSS provider
        if not hasattr(self, '_zoom_provider'):
            self._zoom_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                self.get_display() if self.get_display() else __import__('gi.repository', fromlist=['Gdk']).Gdk.Display.get_default(),
                self._zoom_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
            )

        css = f"""
        .file-grid-view.{css_cls} .file-grid-item {{
            min-width: {cell_px}px;
            min-height: {cell_px}px;
        }}
        .file-grid-view.{css_cls} .file-grid-item image {{
            -gtk-icon-size: {icon_px}px;
        }}
        .file-grid-view.{css_cls} .file-grid-item .thumbnail picture {{
            min-width: {thumb_px}px;
            min-height: {thumb_px}px;
        }}
        .file-grid-view.{css_cls} .file-grid-item .thumbnail {{
            min-width: {thumb_px}px;
            min-height: {thumb_px}px;
        }}
        """
        self._zoom_provider.load_from_string(css)

    def zoom_in(self):
        """Increase icon size."""
        if self._zoom_index < len(self.ZOOM_LEVELS) - 1:
            self._zoom_index += 1
            self._apply_zoom()
            return True
        return False

    def zoom_out(self):
        """Decrease icon size."""
        if self._zoom_index > 0:
            self._zoom_index -= 1
            self._apply_zoom()
            return True
        return False

    def zoom_reset(self):
        """Reset to default zoom."""
        self._zoom_index = 1  # "zoom-normal"
        self._apply_zoom()
