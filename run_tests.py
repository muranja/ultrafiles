# Test Runner
# Sets up global mocks before importing any code.

import sys
import os
from unittest.mock import MagicMock

# 1. Setup Global Mocks for GI (Must do this BEFORE any imports)
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.GObject"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()

# Link submodules so 'from gi.repository import Gio' gets the configured mock
sys.modules["gi.repository"].Gio = sys.modules["gi.repository.Gio"]
sys.modules["gi.repository"].GLib = sys.modules["gi.repository.GLib"]
sys.modules["gi.repository"].GObject = sys.modules["gi.repository.GObject"]
sys.modules["gi.repository"].Gdk = sys.modules["gi.repository.Gdk"]
sys.modules["gi.repository"].Gtk = sys.modules["gi.repository.Gtk"]
sys.modules["gi.repository"].Adw = sys.modules["gi.repository.Adw"]

# Configure specific mock behaviors
# Gio Constants (must be strings for join operations)
gio = sys.modules["gi.repository.Gio"]
gio.FILE_ATTRIBUTE_STANDARD_NAME = "standard::name"
gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME = "standard::display-name"
gio.FILE_ATTRIBUTE_STANDARD_TYPE = "standard::type"
gio.FILE_ATTRIBUTE_STANDARD_SIZE = "standard::size"
gio.FILE_ATTRIBUTE_STANDARD_ICON = "standard::icon"
gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE = "standard::content-type"
gio.FILE_ATTRIBUTE_STANDARD_IS_HIDDEN = "standard::is-hidden"
gio.FILE_ATTRIBUTE_STANDARD_IS_SYMLINK = "standard::is-symlink"
gio.FILE_ATTRIBUTE_TIME_MODIFIED = "time::modified"
gio.FILE_ATTRIBUTE_THUMBNAIL_PATH = "thumbnail::path"
gio.FILE_ATTRIBUTE_ACCESS_CAN_READ = "access::can-read"
gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE = "access::can-write"

# Mock Subprocess flags (integers)
gio.SubprocessFlags.STDOUT_PIPE = 1
gio.SubprocessFlags.STDERR_PIPE = 2
gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS = 0
gio.IOErrorEnum.CANCELLED = 1

sys.modules["gi.repository.GObject"].SignalFlags = MagicMock()

# Define MockGObject to prevent services becoming Mocks
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

# 2. Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    start_dir = 'tests/unit'
    suite = loader.discover(start_dir)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    sys.exit(not result.wasSuccessful())
