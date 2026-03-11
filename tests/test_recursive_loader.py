import unittest
import gi
import os
import shutil
import tempfile
import time
import threading

gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.widgets.file_item import FileItem # Needed for mock/check probably, actually imported by services
from src.services.recursive_loader import RecursiveLoader

class TestRecursiveLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.loader = RecursiveLoader()
        
        # Create structure:
        # root/
        #   image1.jpg
        #   text1.txt
        #   sub/
        #     image2.png
        #     text2.txt
        #     deep/
        #       video.mp4
        
        os.makedirs(os.path.join(self.test_dir, "sub", "deep"))
        
        self.create_file("image1.jpg")
        self.create_file("text1.txt")
        self.create_file("sub/image2.png")
        self.create_file("sub/text2.txt")
        self.create_file("sub/deep/video.mp4")

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        self.loader.cancel()

    def create_file(self, path):
        full_path = os.path.join(self.test_dir, path)
        with open(full_path, 'w') as f:
            f.write("content")

    def test_recursive_media_scan(self):
        root = Gio.File.new_for_path(self.test_dir)
        
        results = []
        done_event = threading.Event()
        
        def callback(items, error):
            if error:
                print(f"Error: {error}")
                done_event.set()
                return
                
            if items is None:
                done_event.set()
                return
                
            results.extend(items)


        self.loader.load_recursive(root, callback, file_filter="media")
        
        # Wait for completion (with timeout)
        # Since GLib.idle_add is used, we need a main loop or similar?
        # Standard unittest doesn't run GLib main loop.
        # We need to simulate the main loop or just wait if passing synchronous.
        # But wait, logic uses GLib.idle_add. If no main loop, it won't run.
        # We need to run a main loop context.
        
        main_context = GLib.MainContext.default()
        
        # Run loop until done
        while not done_event.is_set():
            main_context.iteration(True)
            
        # Verify results
        media_files = {item.name for item in results}
        expected = {"image1.jpg", "image2.png", "video.mp4"}
        
        self.assertEqual(media_files, expected)
        
        # Verify parent names
        for item in results:
            if item.name == "video.mp4":
                self.assertEqual(item.parent_name, "deep")
            if item.name == "image2.png":
                self.assertEqual(item.parent_name, "sub")
            if item.name == "image1.jpg":
                self.assertEqual(item.parent_name, os.path.basename(self.test_dir))

if __name__ == '__main__':
    unittest.main()
