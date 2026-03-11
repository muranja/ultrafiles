# SPDX-License-Identifier: GPL-3.0-or-later
"""
Search Bar Widget
Wrapper around Gtk.SearchEntry with enhanced signals and styling.
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GObject

class SearchBar(Gtk.SearchEntry):
    """
    Search entry for file search.
    """
    __gtype_name__ = "UltraFilesSearchBar"

    def __init__(self):
        super().__init__()
        self.set_placeholder_text("Search files...")
        self.set_width_chars(30)
        # self.connect("search-changed", self._on_search_changed)

    # def _on_search_changed(self, entry):
    #     text = self.get_text()
    #     # Debounce logic could go here
    #     pass
