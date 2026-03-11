
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio

def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    win.set_default_size(800, 600)
    
    # Try to load a known video file if possible, or user can pick.
    # For now, let's just create a button to pick a file.
    
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    win.set_child(box)
    
    picture = Gtk.Picture()
    picture.set_vexpand(True)
    box.append(picture)
    
    controls = Gtk.MediaControls()
    box.append(controls)
    
    def on_open_clicked(btn):
        dialog = Gtk.FileChooserNative(title="Open Video", transient_for=win, action=Gtk.FileChooserAction.OPEN)
        
        def on_response(d, response):
            if response == Gtk.ResponseType.ACCEPT:
                file = d.get_file()
                media = Gtk.MediaFile.new_for_file(file)
                picture.set_paintable(media)
                controls.set_media_stream(media)
                media.set_muted(False)
                media.set_volume(1.0)
                media.play()
                print(f"Playing: {file.get_path()}")
                print(f"Muted: {media.get_muted()}")
                print(f"Volume: {media.get_volume()}")
            d.destroy()
            
        dialog.connect("response", on_response)
        dialog.show()
        
    btn = Gtk.Button(label="Open Video")
    btn.connect("clicked", on_open_clicked)
    box.append(btn)
    
    win.present()

app = Gtk.Application(application_id='org.test.MediaAudio')
app.connect('activate', on_activate)
app.run(None)
