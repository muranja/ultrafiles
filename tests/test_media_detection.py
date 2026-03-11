import unittest
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio
# Mock FileItem to avoid importing the whole app structure if possible, 
# or import it properly if PYTHONPATH is set.
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.widgets.file_item import FileItem

class TestMediaDetection(unittest.TestCase):
    def test_media_detection(self):
        # We need to mock Gio.FileInfo and Gio.File
        # This is hard to mock perfectly without real files, but we can try.
        
        # Strategy: Create temporary files
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            # Write PNG magic bytes
            f.write(b'\x89PNG\r\n\x1a\n')
            f.flush()
            
            gfile = Gio.File.new_for_path(f.name)
            info = gfile.query_info("standard::*,time::*", Gio.FileQueryInfoFlags.NONE, None)
            parent = gfile.get_parent()
            
            item = FileItem(info, parent)
            print(f"Testing PNG: {f.name}, content_type: {item.content_type}")
            self.assertTrue(item.is_image())
            self.assertTrue(item.is_media())

        with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
            # Write MP4 magic bytes (ftyp box)
            f.write(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00')
            f.flush()
            
            gfile = Gio.File.new_for_path(f.name)
            info = gfile.query_info("standard::*,time::*", Gio.FileQueryInfoFlags.NONE, None)
            parent = gfile.get_parent()
            item = FileItem(info, parent)
            print(f"Testing MP4: {f.name}, content_type: {item.content_type}")
            self.assertTrue(item.is_video())
            self.assertTrue(item.is_media())

if __name__ == '__main__':
    unittest.main()
