# SPDX-License-Identifier: GPL-3.0-or-later
"""
Tags Service
Manages file tags and available tag definitions.
"""

import gi
import json
import os
from typing import List, Dict

gi.require_version("GObject", "2.0")
from gi.repository import GObject, GLib

class TagsService(GObject.Object):
    """
    Manages file tags.
    """
    
    __gsignals__ = {
        'tags-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self._config_dir = os.path.join(GLib.get_user_config_dir(), "ultrafiles")
        self._config_file = os.path.join(self._config_dir, "tags.json")
        
        self._available_tags = [
            {"name": "Funny", "color": "#f6d32d"},        # Yellow
            {"name": "Sad", "color": "#62a0ea"},          # Blue
            {"name": "Reaction", "color": "#57e389"},     # Green
            {"name": "Sound Effect", "color": "#ff7800"}, # Orange
            {"name": "Green Screen", "color": "#26a269"}, # Emerald
            {"name": "B-Roll", "color": "#9141ac"},       # Purple
        ]
        self._file_tags = {}
        self._load()

    def _load(self):
        if not os.path.exists(self._config_file):
            return
            
        try:
            with open(self._config_file, 'r') as f:
                data = json.load(f)
                self._available_tags = data.get("available_tags", self._available_tags)
                self._file_tags = data.get("file_tags", {})
        except Exception as e:
            print(f"Error loading tags: {e}")

    def _save(self):
        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir, exist_ok=True)
            
        try:
            with open(self._config_file, 'w') as f:
                json.dump({
                    "available_tags": self._available_tags,
                    "file_tags": self._file_tags
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving tags: {e}")

    def get_available_tags(self) -> List[Dict]:
        return self._available_tags

    def get_tags_for_file(self, uri: str) -> List[str]:
        return self._file_tags.get(uri, [])
        
    def get_tag_color(self, tag_name: str) -> str:
        for tag in self._available_tags:
            if tag["name"] == tag_name:
                return tag["color"]
        return "#ffffff"

    def add_tag(self, uri: str, tag_name: str):
        current = self._file_tags.get(uri, [])
        if tag_name not in current:
            current.append(tag_name)
            self._file_tags[uri] = current
            self._save()
            self.emit("tags-changed")

    def remove_tag(self, uri: str, tag_name: str):
        current = self._file_tags.get(uri, [])
        if tag_name in current:
            current.remove(tag_name)
            if not current:
                del self._file_tags[uri]
            else:
                self._file_tags[uri] = current
            self._save()
            self.emit("tags-changed")

    def toggle_tag(self, uri: str, tag_name: str):
        if tag_name in self.get_tags_for_file(uri):
            self.remove_tag(uri, tag_name)
        else:
            self.add_tag(uri, tag_name)

    def search_by_theme(self, query: str) -> List[str]:
        """Find file URIs with a theme matching the query (case-insensitive)"""
        query = (query or "").strip().lower()
        if not query:
            return []

        matches = []
        for uri, tags in self._file_tags.items():
            for tag in tags:
                if query in tag.lower():
                    matches.append(uri)
                    break
        return matches
