# SPDX-License-Identifier: GPL-3.0-or-later
"""File list view (details view)"""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GLib, GObject, Gdk, Pango

from ..widgets.file_item import FileItem
from ..services.sorting import NaturalSorter


class FileListView(Gtk.Box):
    """List view for files with columns"""

    __gtype_name__ = "UltraFilesListView"

    __gsignals__ = {
        "file-activated": (GObject.SignalFlags.RUN_FIRST, None, (FileItem,)),
        "context-menu-requested": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (float, float, object),
        ),
    }

    def __init__(self, store: Gio.ListStore):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("file-list-view")

        self._store = store
        self._settings = Gio.Settings.new("com.ultrafiles.UltraFiles")

        self._build_ui()

    def _build_ui(self):
        """Build the list view UI"""
        # Cache sort settings to avoid GSettings lookups in comparator
        self._cache_sort_settings()

        # Create sorter
        self._sorter = Gtk.CustomSorter.new(self._compare_files, None)
        self._sort_model = Gtk.SortListModel.new(self._store, self._sorter)
        self._sort_model.set_incremental(True)  # non-blocking sort

        # Selection model
        self._selection = Gtk.MultiSelection.new(self._sort_model)

        # Factory for list items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_setup)
        factory.connect("bind", self._on_bind)
        factory.connect("unbind", self._on_unbind)

        # Create ListView
        self._list_view = Gtk.ListView.new(self._selection, factory)
        self._list_view.set_enable_rubberband(True)
        self._list_view.set_single_click_activate(False)
        self._list_view.add_css_class("rich-list")
        self._list_view.connect("activate", self._on_activate)

        # Right-click for context menu
        right_click = Gtk.GestureClick()
        right_click.set_button(3)  # Right click
        right_click.connect("pressed", self._on_right_click)
        self._list_view.add_controller(right_click)

        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._list_view)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        self.append(scrolled)

    def _on_setup(self, factory, list_item):
        """Create widget structure for list items"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)

        # Icon
        icon = Gtk.Image()
        icon.set_icon_size(Gtk.IconSize.LARGE)
        box.append(icon)
        
        # Git Status
        git_label = Gtk.Label()
        git_label.add_css_class("git-status-label")
        box.append(git_label)

        # Name and info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        name_label = Gtk.Label()
        name_label.set_xalign(0)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_max_width_chars(50)
        info_box.append(name_label)

        type_label = Gtk.Label()
        type_label.set_xalign(0)
        type_label.add_css_class("dim-label")
        type_label.add_css_class("caption")
        info_box.append(type_label)

        box.append(info_box)

        # Size
        size_label = Gtk.Label()
        size_label.add_css_class("dim-label")
        size_label.add_css_class("size-label")
        size_label.set_width_chars(10)
        size_label.set_xalign(1)
        box.append(size_label)

        # Modified date
        date_label = Gtk.Label()
        date_label.add_css_class("dim-label")
        date_label.set_width_chars(16)
        date_label.set_xalign(1)
        box.append(date_label)

        list_item.set_child(box)

    def _on_bind(self, factory, list_item):
        """Bind file data to widgets"""
        box = list_item.get_child()
        item = list_item.get_item()

        # Get widgets
        icon = box.get_first_child()
        git_label = icon.get_next_sibling()
        info_box = git_label.get_next_sibling()
        name_label = info_box.get_first_child()
        type_label = name_label.get_next_sibling()
        size_label = info_box.get_next_sibling()
        date_label = size_label.get_next_sibling()

        # Bind data
        icon.set_from_gicon(item.icon)
        
        # Bind git status
        status = item.git_status
        git_label.set_label("")
        git_label.remove_css_class("git-modified")
        git_label.remove_css_class("git-untracked")
        git_label.remove_css_class("git-ignored")
        
        if status:
            if status == "modified":
                git_label.set_label("M")
                git_label.add_css_class("git-modified")
                git_label.set_tooltip_text("Modified")
            elif status == "untracked":
                git_label.set_label("?")
                git_label.add_css_class("git-untracked")
                git_label.set_tooltip_text("Untracked")
            elif status == "ignored":
                git_label.set_label("!")
                git_label.add_css_class("git-ignored")
                git_label.set_tooltip_text("Ignored")
            elif status == "staged":
                git_label.set_label("A")
                git_label.add_css_class("git-staged")
            elif status == "conflict":
                git_label.set_label("C")
                git_label.add_css_class("git-conflict")

        name_label.set_label(item.display_name)
        type_label.set_label(item.content_type_description)
        size_label.set_label(item.size_formatted)
        date_label.set_label(item.modified_formatted)

        # Store reference for context menu
        box.file_item = item

    def _on_unbind(self, factory, list_item):
        """Unbind data (cleanup)"""
        box = list_item.get_child()
        if hasattr(box, "file_item"):
            del box.file_item

    def _on_activate(self, list_view, position):
        """Handle item activation (double-click/enter)"""
        item = self._selection.get_item(position)
        if item:
            self.emit("file-activated", item)

    def _on_right_click(self, gesture, n_press, x, y):
        """Handle right-click for context menu"""
        # Find item at position
        item = self._get_item_at_position(x, y)
        
        # Translate coordinates from list view to wrapper box
        top_level = self.get_native()
        if top_level:
            # We want coordinates relative to self (the Box)
            # x, y are relative to self._list_view
            res = self._list_view.translate_coordinates(self, x, y)
            if res:
                tx, ty = res
                self.emit("context-menu-requested", tx, ty, item)

    def _get_item_at_position(self, x, y):
        """Get file item at given coordinates"""
        # Convert to list view coordinates
        # This is a simplified approach - in production you'd use pick()
        for i in range(self._selection.get_n_items()):
            if self._selection.is_selected(i):
                return self._selection.get_item(i)
        return None

    def _cache_sort_settings(self):
        """Cache sort settings to avoid GSettings lookups in comparator"""
        self._cached_folders_first = self._settings.get_boolean("folders-first")
        self._cached_sort_by = self._settings.get_string("sort-by")
        self._cached_ascending = self._settings.get_boolean("sort-ascending")

    def _compare_files(self, item_a, item_b, user_data):
        """Compare function for sorting files (uses cached settings)"""
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
        bitset = self._selection.get_selection()
        # PyGObject makes GtkBitset iterable
        try:
             for pos in bitset:
                 item = self._selection.get_item(pos)
                 if item:
                     items.append(item)
        except TypeError:
             # Fallback if not iterable (older overrides?)
             # Gtk.BitsetIter usage
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
