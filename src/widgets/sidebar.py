# SPDX-License-Identifier: GPL-3.0-or-later
"""Sidebar widget with places navigation"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk, GObject
from .directory_tree import DirectoryTree


class Sidebar(Gtk.Box):
    """Sidebar with places, devices, and bookmarks"""

    __gtype_name__ = "UltraFilesSidebar"

    __gsignals__ = {
        "place-selected": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self._settings = Gio.Settings.new("com.ultrafiles.UltraFiles")
        self._build_ui()

    def _build_ui(self):
        """Build the sidebar UI"""
        # Header
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_title_widget(Gtk.Label(label="Places"))
        self.append(header)

        # Scrollable content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        self.append(scrolled)

        # Main container
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_box.set_margin_start(6)
        content_box.set_margin_end(6)
        content_box.set_margin_top(6)
        content_box.set_margin_bottom(6)
        scrolled.set_child(content_box)

        # Directory Tree Section
        header = Gtk.Label(label="Folders")
        header.add_css_class("section-header")
        header.set_xalign(0)
        header.set_margin_top(6)
        header.set_margin_bottom(6)
        content_box.append(header)

        self._tree = DirectoryTree()
        self._tree.connect("directory-selected", self._on_tree_selection)
        content_box.append(self._tree)

        # Places section
        self._add_section(content_box, "Places", self._get_standard_places())

        # Favorites (Starred) section
        self._favorites_listbox = self._add_section(content_box, "Favorites", [])
        
        # Devices section (if any)
        devices = self._get_devices()
        if devices:
            self._add_section(content_box, "Devices", devices)

        # Bookmarks section
        bookmarks = self._get_bookmarks()
        if bookmarks:
            self._add_section(content_box, "Bookmarks", bookmarks)

    def _add_section(self, parent: Gtk.Box, title: str, places: list):
        """Add a section with title and places list"""
        # Section header
        header = Gtk.Label(label=title)
        header.add_css_class("section-header")
        header.set_xalign(0)
        header.set_margin_top(12)
        header.set_margin_bottom(6)
        parent.append(header)

        # Places list
        listbox = Gtk.ListBox()
        listbox.add_css_class("navigation-sidebar")
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.connect("row-activated", self._on_row_activated)
        parent.append(listbox)

        for place in places:
            row = self._create_place_row(place)
            listbox.append(row)
            
        return listbox

    def _create_place_row(self, place: dict) -> Gtk.ListBoxRow:
        """Create a row for a place"""
        row = Gtk.ListBoxRow()
        row.place_path = place["path"]

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.set_margin_top(8)
        box.set_margin_bottom(8)

        icon = Gtk.Image.new_from_icon_name(place["icon"])
        box.append(icon)

        label = Gtk.Label(label=place["name"])
        label.set_xalign(0)
        label.set_hexpand(True)
        box.append(label)

        row.set_child(box)
        return row

    def _get_standard_places(self) -> list:
        """Get standard places (Home, Docs, etc)"""
        places = []

        # Home
        home = GLib.get_home_dir()
        if home:
            places.append({"name": "Home", "path": home, "icon": "user-home-symbolic"})

        # Standard user directories
        user_dirs = [
            (
                GLib.UserDirectory.DIRECTORY_DOCUMENTS,
                "Documents",
                "folder-documents-symbolic",
            ),
            (
                GLib.UserDirectory.DIRECTORY_DOWNLOAD,
                "Downloads",
                "folder-download-symbolic",
            ),
            (GLib.UserDirectory.DIRECTORY_MUSIC, "Music", "folder-music-symbolic"),
            (
                GLib.UserDirectory.DIRECTORY_PICTURES,
                "Pictures",
                "folder-pictures-symbolic",
            ),
            (GLib.UserDirectory.DIRECTORY_VIDEOS, "Videos", "folder-videos-symbolic"),
        ]

        for dir_type, name, icon in user_dirs:
            path = GLib.get_user_special_dir(dir_type)
            if path and path != home:  # Skip if same as home
                places.append({"name": name, "path": path, "icon": icon})

        # Trash
        places.append(
            {"name": "Trash", "path": "trash:///", "icon": "user-trash-symbolic"}
        )

        return places

    def _get_devices(self) -> list:
        """Get mounted devices/volumes"""
        places = []

        # Root filesystem
        places.append(
            {"name": "Computer", "path": "/", "icon": "drive-harddisk-symbolic"}
        )

        # Get volume monitor for mounted volumes
        monitor = Gio.VolumeMonitor.get()

        for mount in monitor.get_mounts():
            root = mount.get_root()
            if root:
                path = root.get_path()
                if path and path != "/":
                    places.append(
                        {
                            "name": mount.get_name(),
                            "path": path,
                            "icon": "drive-removable-media-symbolic",
                        }
                    )

        return places

    def _get_bookmarks(self) -> list:
        """Get user bookmarks"""
        places = []
        bookmark_paths = self._settings.get_strv("bookmarks")

        for path in bookmark_paths:
            gfile = Gio.File.new_for_path(path)
            if gfile.query_exists():
                places.append(
                    {
                        "name": gfile.get_basename(),
                        "path": path,
                        "icon": "folder-symbolic",
                    }
                )

        return places

    def _on_row_activated(self, listbox, row):
        """Handle place selection"""
        if hasattr(row, "place_path"):
            self.emit("place-selected", row.place_path)

    def add_bookmark(self, path: str):
        """Add a bookmark"""
        bookmarks = list(self._settings.get_strv("bookmarks"))
        if path not in bookmarks:
            bookmarks.append(path)
            self._settings.set_strv("bookmarks", bookmarks)
            # Rebuild UI to show new bookmark
            # For simplicity, we could emit a signal or refresh

    def remove_bookmark(self, path: str):
        """Remove a bookmark"""
        bookmarks = list(self._settings.get_strv("bookmarks"))
        if path in bookmarks:
            bookmarks.remove(path)
            self._settings.set_strv("bookmarks", bookmarks)

    def update_favorites(self, uris: list):
        """Update user favorites section"""
        # Clear existing
        while True:
            row = self._favorites_listbox.get_first_child()
            if not row:
                break
            self._favorites_listbox.remove(row)
            
        # Add new
        for uri in uris:
            try:
                gfile = Gio.File.new_for_uri(uri)
                name = gfile.get_basename()
                path = gfile.get_path() or uri
                
                place = {
                    "name": name,
                    "path": path,
                    "icon": "starred-symbolic" # or "emblem-favorite"
                }
                
                row = self._create_place_row(place)
                self._favorites_listbox.append(row)
            except Exception:
                pass

    def _on_tree_selection(self, tree, path):
         """Handle tree selection"""
         self.emit("place-selected", path)
