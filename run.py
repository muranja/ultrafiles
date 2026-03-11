#!/usr/bin/env python3
import sys
import os

# Force software rendering for compatibility
os.environ["GSK_RENDERER"] = "cairo"

import gi
# Require Gst version to trigger hook
try:
    gi.require_version("Gst", "1.0")
    from gi.repository import Gio, GLib, Gst
except ValueError:
    from gi.repository import Gio, GLib

# Handle PyInstaller resources
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    
    # 1. Set Schema Directory
    # Must be set before GSettings is initialized
    if os.path.exists(os.path.join(base_path, 'gschemas.compiled')):
        os.environ["GSETTINGS_SCHEMA_DIR"] = base_path
        
    # 2. Register GResource
    resource_path = os.path.join(base_path, 'ultrafiles.gresource')
    if os.path.exists(resource_path):
        try:
            res = Gio.Resource.load(resource_path)
            res._register()
        except Exception as e:
            print(f"Failed to register resource: {e}")

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.main import main
from src import __version__

if __name__ == "__main__":
    sys.exit(main(__version__))
