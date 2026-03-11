# Pytest configuration: mock GI modules before imports
import sys
import os
from unittest.mock import MagicMock


def _install_gi_mocks():
    if "gi" in sys.modules:
        return

    sys.modules["gi"] = MagicMock()
    sys.modules["gi.repository"] = MagicMock()
    sys.modules["gi.repository.Gio"] = MagicMock()
    sys.modules["gi.repository.GLib"] = MagicMock()
    sys.modules["gi.repository.GObject"] = MagicMock()
    sys.modules["gi.repository.Gdk"] = MagicMock()
    sys.modules["gi.repository.Gtk"] = MagicMock()
    sys.modules["gi.repository.Adw"] = MagicMock()

    sys.modules["gi.repository"].Gio = sys.modules["gi.repository.Gio"]
    sys.modules["gi.repository"].GLib = sys.modules["gi.repository.GLib"]
    sys.modules["gi.repository"].GObject = sys.modules["gi.repository.GObject"]
    sys.modules["gi.repository"].Gdk = sys.modules["gi.repository.Gdk"]
    sys.modules["gi.repository"].Gtk = sys.modules["gi.repository.Gtk"]
    sys.modules["gi.repository"].Adw = sys.modules["gi.repository.Adw"]

    gio = sys.modules["gi.repository.Gio"]
    gio.FILE_ATTRIBUTE_STANDARD_NAME = "standard::name"
    gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME = "standard::display-name"
    gio.FILE_ATTRIBUTE_STANDARD_TYPE = "standard::type"
    gio.FILE_ATTRIBUTE_STANDARD_SIZE = "standard::size"
    gio.FILE_ATTRIBUTE_STANDARD_ICON = "standard::icon"
    gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE = "standard::content-type"
    gio.FILE_ATTRIBUTE_STANDARD_FAST_CONTENT_TYPE = "standard::fast-content-type"
    gio.FILE_ATTRIBUTE_STANDARD_IS_HIDDEN = "standard::is-hidden"
    gio.FILE_ATTRIBUTE_STANDARD_IS_SYMLINK = "standard::is-symlink"
    gio.FILE_ATTRIBUTE_TIME_MODIFIED = "time::modified"
    gio.FILE_ATTRIBUTE_THUMBNAIL_PATH = "thumbnail::path"
    gio.FILE_ATTRIBUTE_ACCESS_CAN_READ = "access::can-read"
    gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE = "access::can-write"

    gio.SubprocessFlags.STDOUT_PIPE = 1
    gio.SubprocessFlags.STDERR_PIPE = 2
    gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS = 0
    gio.IOErrorEnum.CANCELLED = 1

    sys.modules["gi.repository.GObject"].SignalFlags = MagicMock()

    class MockGObject:
        def __init__(self, *args, **kwargs):
            pass
        def emit(self, *args):
            pass
        def notify(self, *args):
            pass
        def connect(self, *args):
            pass
        @classmethod
        def install_property(cls, *args, **kwargs):
            pass

    sys.modules["gi.repository.GObject"].Object = MockGObject


_install_gi_mocks()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
