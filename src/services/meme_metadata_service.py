# SPDX-License-Identifier: GPL-3.0-or-later
"""
Meme Metadata Service
Stores meme-specific metadata (captions/transcripts) in SQLite.
"""

import gi
import os
import sqlite3
from typing import List

gi.require_version("GObject", "2.0")
from gi.repository import GObject, GLib


class MemeMetadataService(GObject.Object):
    """
    Stores and searches meme-specific metadata.
    """

    def __init__(self):
        super().__init__()
        self._config_dir = os.path.join(GLib.get_user_config_dir(), "ultrafiles")
        self._db_path = os.path.join(self._config_dir, "meme_data.db")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self):
        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir, exist_ok=True)
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS meme_metadata (
                        uri TEXT PRIMARY KEY,
                        caption TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_meme_caption ON meme_metadata(caption)"
                )
        except Exception as e:
            print(f"Error initializing meme metadata DB: {e}")

    def get_caption(self, uri: str) -> str:
        """Get caption for a file URI"""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT caption FROM meme_metadata WHERE uri = ?",
                    (uri,),
                ).fetchone()
                return row[0] if row else ""
        except Exception as e:
            print(f"Error reading caption: {e}")
            return ""

    def set_caption(self, uri: str, caption: str) -> bool:
        """Set or clear caption for a file URI"""
        caption = (caption or "").strip()
        try:
            with self._connect() as conn:
                if not caption:
                    conn.execute("DELETE FROM meme_metadata WHERE uri = ?", (uri,))
                else:
                    conn.execute(
                        "INSERT OR REPLACE INTO meme_metadata (uri, caption) VALUES (?, ?)",
                        (uri, caption),
                    )
            return True
        except Exception as e:
            print(f"Error saving caption: {e}")
            return False

    def search_captions(self, query: str) -> List[str]:
        """Search captions for query (case-insensitive), return matching URIs"""
        query = (query or "").strip()
        if not query:
            return []
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT uri FROM meme_metadata WHERE caption LIKE ? COLLATE NOCASE",
                    (f"%{query}%",),
                ).fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print(f"Error searching captions: {e}")
            return []
