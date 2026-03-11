# SPDX-License-Identifier: GPL-3.0-or-later
"""FileItem - GObject wrapper for file information"""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gio, GLib


class FileItem(GObject.Object):
    """GObject wrapper for file information to use in GListModel"""

    __gtype_name__ = "FileItem"
    
    # Store git status as a property
    # Values: "modified", "untracked", "ignored", "staged", "conflict", or ""
    git_status = GObject.Property(type=str, default="")

    def __init__(self, file_info: Gio.FileInfo, parent_file: Gio.File):
        super().__init__()
        self._info = file_info
        self._gfile = parent_file.get_child(file_info.get_name())

    @GObject.Property(type=str)
    def name(self) -> str:
        """File name"""
        return self._info.get_name()

    @GObject.Property(type=str)
    def display_name(self) -> str:
        """Display name (may differ from name for special files)"""
        return self._info.get_display_name()

    @GObject.Property(type=str)
    def path(self) -> str:
        """Full file path"""
        return self._gfile.get_path() or ""

    @GObject.Property(type=str)
    def uri(self) -> str:
        """File URI"""
        return self._gfile.get_uri()

    @GObject.Property(type=bool, default=False)
    def is_directory(self) -> bool:
        """Whether this is a directory"""
        return self._info.get_file_type() == Gio.FileType.DIRECTORY

    @GObject.Property(type=bool, default=False)
    def is_hidden(self) -> bool:
        """Whether this is a hidden file"""
        return self._info.get_is_hidden()

    @GObject.Property(type=bool, default=False)
    def is_symlink(self) -> bool:
        """Whether this is a symbolic link"""
        return self._info.get_is_symlink()

    @GObject.Property(type=GObject.TYPE_INT64)
    def size(self) -> int:
        """File size in bytes"""
        return self._info.get_size()

    @GObject.Property(type=str)
    def size_formatted(self) -> str:
        """Human-readable file size"""
        if self.is_directory:
            return ""
        return GLib.format_size(self._info.get_size())

    @GObject.Property(type=GObject.TYPE_INT64)
    def modified_time(self) -> int:
        """Modification time as Unix timestamp"""
        dt = self._info.get_modification_date_time()
        return dt.to_unix() if dt else 0

    @GObject.Property(type=str)
    def modified_formatted(self) -> str:
        """Human-readable modification time"""
        dt = self._info.get_modification_date_time()
        if dt:
            return dt.format("%Y-%m-%d %H:%M")
        return ""

    @GObject.Property(type=str)
    def content_type(self) -> str:
        """MIME content type (fast, extension-based)"""
        # Prefer fast content type (extension-based, no file header I/O)
        ct = self._info.get_attribute_string("standard::fast-content-type")
        if ct:
            return ct
        # Fallback to full content type if available
        return self._info.get_content_type() or "application/octet-stream"

    @GObject.Property(type=str)
    def content_type_description(self) -> str:
        """Human-readable content type description"""
        content_type = self.content_type
        return Gio.content_type_get_description(content_type) or content_type

    @GObject.Property(type=Gio.Icon)
    def icon(self) -> Gio.Icon:
        """File icon"""
        return self._info.get_icon()

    @GObject.Property(type=str)
    def thumbnail_path(self) -> str:
        """Path to thumbnail if available"""
        return getattr(self, '_thumbnail_path', '') or ''
        
    def set_thumbnail_path(self, path: str):
        """Set thumbnail path manually"""
        if path:
            self._thumbnail_path = path
            self.notify("thumbnail-path")

    @GObject.Property(type=bool, default=False)
    def is_favorite(self):
        """Standard python attribute backed property"""
        return getattr(self, "_is_favorite", False)

    @is_favorite.setter
    def is_favorite(self, value):
        self._is_favorite = value
        self.notify("is-favorite")

    @GObject.Property(type=object)
    def tags(self):
        """List of tag names"""
        return getattr(self, "_tags", [])

    @tags.setter
    def tags(self, value):
        self._tags = value
        self.notify("tags")

    @property
    def gfile(self) -> Gio.File:
        """Get the underlying GFile"""
        return self._gfile

    @property
    def file_info(self) -> Gio.FileInfo:
        """Get the underlying GFileInfo"""
        return self._info

    def get_extension(self) -> str:
        """Get file extension (lowercase, without dot)"""
        name = self.name
        if "." in name:
            return name.rsplit(".", 1)[-1].lower()
        return ""

    def is_media(self) -> bool:
        """Check if this is a media file (image/video/audio)"""
        content_type = self.content_type
        return (
            content_type.startswith("image/")
            or content_type.startswith("video/")
            or content_type.startswith("audio/")
        )

    def is_image(self) -> bool:
        """Check if this is an image file"""
        return self.content_type.startswith("image/")

    def is_video(self) -> bool:
        """Check if this is a video file"""
        return self.content_type.startswith("video/")

    def is_audio(self) -> bool:
        """Check if this is an audio file"""
        return self.content_type.startswith("audio/")

    def is_pdf(self) -> bool:
        """Check if this is a PDF file"""
        return self.content_type == "application/pdf"

    def is_text(self) -> bool:
        """Check if this is a text file"""
        content_type = self.content_type
        return content_type.startswith("text/") or content_type in [
            "application/json",
            "application/xml",
            "application/javascript",
            "application/x-shellscript",
        ]

    def is_archive(self) -> bool:
        """Check if this is an archive file"""
        content_type = self.content_type
        return content_type in [
            "application/zip",
            "application/x-tar",
            "application/gzip",
            "application/x-bzip2",
            "application/x-xz",
            "application/x-7z-compressed",
            "application/x-rar-compressed",
            "application/vnd.rar",
        ]
    @GObject.Property(type=str)
    def parent_name(self) -> str:
        """Name of the parent directory"""
        parent = self._gfile.get_parent()
        if parent:
            return parent.get_basename() or ""
        return ""
