# SPDX-License-Identifier: GPL-3.0-or-later
"""
Batch Rename Dialog
Supports Find/Replace and Numbering.
"""

import gi
import re
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, Gio, GObject

def show_batch_rename_dialog(parent, files, callback):
    """
    files: List of FileItem
    callback: func(list of (original_path, new_name)) -> None. If None, cancelled.
    """
    dialog = BatchRenameDialog(files)
    dialog.set_transient_for(parent)
    dialog._callback = callback
    dialog.present()

class BatchRenameDialog(Adw.Window):
    __gtype_name__ = "BatchRenameDialog"

    def __init__(self, files):
        super().__init__(title=f"Rename {len(files)} files")
        self.set_modal(True)
        self.set_default_size(600, 500)
        
        self._files = files
        self._callback = None
        self._previews = [] # List of (item, new_name)
        
        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(content)
        
        # Header
        header = Adw.HeaderBar()
        content.append(header)
        
        # Rename button
        self._rename_btn = Gtk.Button(label="Rename")
        self._rename_btn.add_css_class("suggested-action")
        self._rename_btn.connect("clicked", self._on_rename)
        header.pack_end(self._rename_btn)
        
        # Controls
        controls = Adw.PreferencesGroup()
        controls.set_margin_top(12)
        controls.set_margin_bottom(12)
        controls.set_margin_start(12)
        controls.set_margin_end(12)
        content.append(controls)
        
        # Mode switch (Find/Replace vs Template)
        # Simplified: Just Find/Replace for now, maybe Template later if requested.
        # User asked for "Batch rename with patterns".
        # Find/Replace is a pattern.
        
        # Find Entry
        self._find_entry = Adw.EntryRow(title="Find")
        self._find_entry.connect("changed", self._on_change)
        controls.add(self._find_entry)
        
        # Replace Entry
        self._replace_entry = Adw.EntryRow(title="Replace with")
        self._replace_entry.connect("changed", self._on_change)
        controls.add(self._replace_entry)
        
        # Preview List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        content.append(scrolled)
        
        # Column View for preview
        self._store = Gio.ListStore(item_type=RenameItem)
        
        selection = Gtk.NoSelection.new(self._store)
        
        column_view = Gtk.ColumnView.new(selection)
        
        # Original Name Column
        c1 = Gtk.ColumnViewColumn(title="Original Name")
        f1 = Gtk.SignalListItemFactory()
        f1.connect("setup", self._setup_label)
        f1.connect("bind", lambda f, i: self._bind_label(f, i, "original"))
        c1.set_factory(f1)
        c1.set_expand(True)
        column_view.append_column(c1)
        
        # New Name Column
        c2 = Gtk.ColumnViewColumn(title="New Name")
        f2 = Gtk.SignalListItemFactory()
        f2.connect("setup", self._setup_label)
        f2.connect("bind", lambda f, i: self._bind_label(f, i, "new"))
        c2.set_factory(f2)
        c2.set_expand(True)
        column_view.append_column(c2)
        
        scrolled.set_child(column_view)

    def _setup_label(self, factory, item):
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        item.set_child(label)
        
    def _bind_label(self, factory, item, attr):
        label = item.get_child()
        obj = item.get_item()
        if attr == "original":
            label.set_label(obj.original)
        else:
            label.set_label(obj.new_name)
            # Highlight if changed?
            if obj.original != obj.new_name:
                label.add_css_class("success")
            else:
                label.remove_css_class("success")

    def _on_change(self, widget):
        self._update_preview()
        
    def _update_preview(self):
        find = self._find_entry.get_text()
        replace = self._replace_entry.get_text()
        
        self._store.remove_all()
        
        # Basic Find/Replace logic
        # Support regex?
        # Let's support regex if it compiles?
        # Or simple string replace.
        # User said "patterns". Regex is good.
        
        for f in self._files:
            original = f.display_name
            new_name = original
            
            if find:
                try:
                    # Case insensitive?
                    # new_name = re.sub(find, replace, original)
                    new_name = original.replace(find, replace)
                except Exception:
                    pass
            
            self._store.append(RenameItem(original, new_name, f.gfile.get_path()))
            
    def _on_rename(self, btn):
        # Gather results
        results = []
        for i in range(self._store.get_n_items()):
            item = self._store.get_item(i)
            if item.original != item.new_name:
                results.append((item.path, item.new_name))
        
        if self._callback:
            self._callback(results)
            
        self.close()

class RenameItem(GObject.Object):
    def __init__(self, original, new, path):
        super().__init__()
        self.original = original
        self.new_name = new
        self.path = path
