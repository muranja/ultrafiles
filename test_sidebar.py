import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, Adw
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Setup GSchema
schema_dir = os.path.join(os.getcwd(), 'data')
if os.path.exists(os.path.join(schema_dir, 'gschemas.compiled')):
    os.environ['GSETTINGS_SCHEMA_DIR'] = schema_dir
    
# Mock missing modules if necessary, but we try real first
from widgets.sidebar import Sidebar

def on_place_selected(sidebar, path):
    print(f"Place selected: {path}")

def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    win.set_title("Sidebar Test")
    win.set_default_size(300, 600)

    sidebar = Sidebar()
    sidebar.connect("place-selected", on_place_selected)
    
    win.set_child(sidebar)
    win.present()

app = Adw.Application(application_id="com.example.SidebarTest")
app.connect("activate", on_activate)
app.run(None)
