import sys
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, Adw

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.viewers.media_viewer import MediaViewer
from src.widgets.file_item import FileItem

def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    win.set_title("MediaViewer Component Test")
    win.set_default_size(800, 600)

    # Create dummy file items
    image_path = "/home/vin/Downloads/CS 1102 PA U2 Image.png"
    video_path = "/home/vin/Downloads/twitter_cнєєкυ⋆｡🪐˚ ⋆(@Okay_Bye___)_20260213-150129_2022325259094138970_video.mp4"

    items = []

    # Helper to create item
    def create_item(path):
        try:
            f = Gio.File.new_for_path(path)
            # We need info for FileItem constructor
            info = f.query_info("standard::*,time::*", Gio.FileQueryInfoFlags.NONE, None)
            return FileItem(info, f.get_parent())
        except Exception as e:
            print(f"Error creating item for {path}: {e}")
            return None

    img_item = create_item(image_path)
    if img_item: items.append(img_item)
    
    vid_item = create_item(video_path)
    if vid_item: items.append(vid_item)

    if not items:
        print("No items found to test!")
        return

    # Instantiate Viewer
    print(f"Creating MediaViewer with {len(items)} items")
    viewer = MediaViewer(items, 1) # Start with second item (video)
    
    win.set_child(viewer)
    win.present()

app = Adw.Application(application_id='com.example.component_test')
app.connect('activate', on_activate)
app.run(None)
