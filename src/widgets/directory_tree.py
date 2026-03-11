# SPDX-License-Identifier: GPL-3.0-or-later
"""Directory Tree Widget"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject
import os

class DirectoryTree(Gtk.Box):
    """Widget for displaying a directory tree"""
    
    __gtype_name__ = "DirectoryTree"

    __gsignals__ = {
        "directory-selected": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self._build_ui()
        
        # Load home by default
        self.set_root_path(GLib.get_home_dir())

    def _build_ui(self):
        """Build the UI"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        self.append(scrolled)

        # Factory for tree rows
        self._factory = Gtk.SignalListItemFactory()
        self._factory.connect("setup", self._on_setup)
        self._factory.connect("bind", self._on_bind)

        # Selection model
        self._selection = Gtk.SingleSelection()
        self._selection.set_autoselect(False)
        self._selection.connect("notify::selected-item", self._on_selection_changed)
        
        # List View
        self._list_view = Gtk.ListView(model=self._selection, factory=self._factory)
        self._list_view.add_css_class("navigation-sidebar")
        scrolled.set_child(self._list_view)

    def set_root_path(self, path: str):
        """Set the root path for the tree"""
        if not path or not os.path.exists(path):
            return

        # Create root item
        root_file = Gio.File.new_for_path(path)
        # We wrap the root file in our custom object to be consistent
        root_obj = DirectoryItem(root_file)
        
        # Create a ListStore for the root level containing just the root object
        # This allows us to have a single root node in the tree if we want (like "Home")
        # OR we can list the content of root directly.
        # GtkTreeListModel usually takes a model of root items.
        # If we want "Home" to be expandable, we need a model containing "Home".
        
        root_store = Gio.ListStore.new(DirectoryItem)
        root_store.append(root_obj)

        self._tree_model = Gtk.TreeListModel.new(
            root_store,
            False, # passthrough (False = items are nodes)
            True,  # autoexpand
            self._create_child_model
        )
        
        self._selection.set_model(self._tree_model)

    def _create_child_model(self, item: GObject.Object) -> Gtk.SortListModel:
        """Create model for a child node"""
        if not isinstance(item, DirectoryItem):
             return None
             
        # Create DirectoryList for this item
        dl = Gtk.DirectoryList.new(
            "standard::name,standard::display-name,standard::icon,standard::type,standard::is-hidden,standard::is-symlink",
            item.gfile
        )
        
        # We need to map FileInfo -> DirectoryItem
        # Problem: map_func user_data is fixed when model created?
        # Yes. But here we create a NEW model for each directory. 
        # So we can pass the parent DirectoryItem or GFile as user_data!
        
        # Create a Python callback that captures the parent file
        # We need to be careful about closure binding.
        parent_file = item.gfile
        
        def map_func(info):
            name = info.get_name()
            child = parent_file.get_child(name)
            return DirectoryItem(child, info)

        map_model = Gtk.MapListModel.new(dl, map_func)
        
        # Filter (Directories only, no hidden)
        fl = Gtk.FilterListModel.new(map_model, None)
        
        # Define filter func
        def filter_func(item, user_data):
            if not isinstance(item, DirectoryItem):
                return False
            if item.is_hidden:
                return False
            if not item.is_directory:
                return False
            return True

        f = Gtk.CustomFilter.new(filter_func, None)
        fl.set_filter(f)
        
        # Sort (Name)
        sl = Gtk.SortListModel.new(fl, None)
        sorter = Gtk.StringSorter(expression=Gtk.PropertyExpression.new(DirectoryItem, None, "name"))
        sl.set_sorter(sorter)
        
        return sl

    def _on_setup(self, factory, list_item):
        """Setup row"""
        expander = Gtk.TreeExpander()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        icon = Gtk.Image()
        box.append(icon)
        
        label = Gtk.Label()
        label.set_xalign(0)
        label.set_hexpand(True)
        label.set_ellipsize(3) # Pango.EllipsizeMode.END
        box.append(label)
        
        expander.set_child(box)
        list_item.set_child(expander)

    def _on_bind(self, factory, list_item):
        """Bind row"""
        expander = list_item.get_child()
        box = expander.get_child()
        icon = box.get_first_child()
        label = icon.get_next_sibling()
        
        # TreeListRow wrapper
        row = list_item.get_item() 
        # Item inside is DirectoryItem
        item = row.get_item() 
        
        expander.set_list_row(row)
        
        if isinstance(item, DirectoryItem):
             label.set_label(item.display_name)
             icon.set_from_gicon(item.icon)

    def _on_selection_changed(self, selection, pspec):
        """Handle selection"""
        row = selection.get_selected_item()
        if row:
            # Row is TreeListRow
            item = row.get_item()
            if isinstance(item, DirectoryItem):
                self.emit("directory-selected", item.path)


class DirectoryItem(GObject.Object):
    """Wrapper for GFile/GFileInfo to use in TreeListModel"""
    
    __gtype_name__ = "DirectoryItem"
    
    def __init__(self, gfile: Gio.File, info: Gio.FileInfo = None):
        super().__init__()
        self._gfile = gfile
        self._info = info
        
        if not self._info:
            # Query sync if info not provided (e.g. root)
             try:
                 self._info = self._gfile.query_info(
                     "standard::name,standard::display-name,standard::icon,standard::type,standard::is-hidden",
                     Gio.FileQueryInfoFlags.NONE,
                     None
                 )
             except Exception:
                 pass

    @GObject.Property(type=str)
    def name(self) -> str:
        return self._info.get_name() if self._info else self._gfile.get_basename()

    @GObject.Property(type=str)
    def display_name(self) -> str:
        return self._info.get_display_name() if self._info else self._gfile.get_basename()

    @GObject.Property(type=str)
    def path(self) -> str:
        return self._gfile.get_path()

    @GObject.Property(type=Gio.Icon)
    def icon(self) -> Gio.Icon:
        # Check if we have standard icon first
        if self._info:
             return self._info.get_icon()
        return Gio.ThemedIcon.new("folder-symbolic")

    @property
    def is_directory(self) -> bool:
        if self._info:
            return self._info.get_file_type() == Gio.FileType.DIRECTORY
        return True # Default assumption for root

    @property
    def is_hidden(self) -> bool:
        if self._info:
            return self._info.get_is_hidden()
        return False
        
    @property
    def gfile(self) -> Gio.File:
        return self._gfile
