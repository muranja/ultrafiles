# SPDX-License-Identifier: GPL-3.0-or-later
"""
Favorites Service
Manages list of favorite files/folders using JSON storage.
"""

import gi
import json
import os
from typing import List

gi.require_version("GObject", "2.0")
from gi.repository import GObject, GLib, Gio

class FavoritesService(GObject.Object):
    """
    Manages user favorites.
    signals:
        changed: ()
    """
    
    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self._config_dir = os.path.join(GLib.get_user_config_dir(), "ultrafiles")
        self._config_file = os.path.join(self._config_dir, "favorites.json")
        self._favorites = set()
        self._load()

    def _load(self):
        """Load favorites from JSON"""
        if not os.path.exists(self._config_file):
            return
            
        try:
            with open(self._config_file, 'r') as f:
                data = json.load(f)
                self._favorites = set(data.get("favorites", []))
        except Exception as e:
            print(f"Error loading favorites: {e}")

    def _save(self):
        """Save favorites to JSON"""
        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir, exist_ok=True)
            
        try:
            with open(self._config_file, 'w') as f:
                json.dump({"favorites": list(self._favorites)}, f, indent=2)
        except Exception as e:
            print(f"Error saving favorites: {e}")

    def add_favorite(self, uri: str):
        """Add URI to favorites"""
        if uri not in self._favorites:
            self._favorites.add(uri)
            self._save()
            self.emit("changed")

    def remove_favorite(self, uri: str):
        """Remove URI from favorites"""
        if uri in self._favorites:
            self._favorites.remove(uri)
            self._save()
            self.emit("changed")

    def is_favorite(self, uri: str) -> bool:
        """Check if URI is favorite"""
        return uri in self._favorites

    def get_favorites(self) -> List[str]:
        """Get list of favorite URIs"""
        return list(self._favorites)
        
    def toggle_favorite(self, uri: str):
        """Toggle favorite state"""
        if self.is_favorite(uri):
            self.remove_favorite(uri)
        else:
            self.add_favorite(uri)
