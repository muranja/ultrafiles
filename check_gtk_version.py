import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

print(f"Gtk version: {Gtk.get_major_version()}.{Gtk.get_minor_version()}")
try:
    print(f"Gtk.FileDialog available: {hasattr(Gtk, 'FileDialog')}")
except:
    pass
