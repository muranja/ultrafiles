# SPDX-License-Identifier: GPL-3.0-or-later
"""
Metadata Service
Handles reading and writing metadata tags using mutagen.
Adheres to strict rails (error handling, type safety).
"""

import gi
from typing import Dict, Any, Optional
import os

gi.require_version("GObject", "2.0")
from gi.repository import GObject, GLib

# Try importing mutagen
try:
    import mutagen
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

class MetadataService(GObject.Object):
    """
    Service for reading/writing file metadata.
    """
    
    def __init__(self):
        super().__init__()

    def is_available(self) -> bool:
        return MUTAGEN_AVAILABLE

    def read_metadata(self, path: str) -> Dict[str, str]:
        """Read metadata tags from file"""
        if not MUTAGEN_AVAILABLE:
            return {}
            
        try:
            # mutagen.File usually detects type
            f = mutagen.File(path)
            if not f:
                return {}
                
            tags = {}
            # EasyID3 maps common keys nicely
            if isinstance(f, MP3):
                 # Use EasyID3 for simple dict access
                 try:
                     f = EasyID3(path)
                 except Exception:
                     pass # Fallback to raw tags?
            
            # Extract common tags
            # Keys: title, artist, album, date, genre, tracknumber
            # Mutagen keys vary. EasyID3 standardizes.
            # FLAC uses VorbisComments (TITLE, ARTIST).
            
            # Helper to get first value
            def get(key):
                val = f.get(key) or f.get(key.upper())
                if val:
                    return str(val[0])
                return ""
            
            tags["title"] = get("title")
            tags["artist"] = get("artist")
            tags["album"] = get("album")
            tags["year"] = get("date") or get("year")
            tags["genre"] = get("genre")
            tags["track"] = get("tracknumber")
            
            return tags
            
        except Exception as e:
            print(f"Error reading metadata: {e}")
            return {}

    def write_metadata(self, path: str, tags: Dict[str, str]) -> bool:
        """Write metadata tags to file"""
        if not MUTAGEN_AVAILABLE:
            return False
            
        try:
            f = mutagen.File(path)
            if not f:
                return False
                
            # For MP3, ensure ID3 tags exist
            if isinstance(f, MP3):
                try:
                    f = EasyID3(path)
                except mutagen.id3.ID3NoHeaderError:
                     f = EasyID3()
                     f.save(path)
                     f = EasyID3(path)
            
            # Update tags
            for key, value in tags.items():
                if value:
                     f[key] = value
                else:
                     # Remove if empty? Or delete key
                     if key in f:
                         del f[key]
            
            f.save()
            return True
            
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
