# SPDX-License-Identifier: GPL-3.0-or-later
"""
Terminal Panel Widget
Wrapper around Vte.Terminal.
"""

import gi
import os

gi.require_version("Gtk", "4.0")

try:
    # Try to load Vte but ensure it doesn't conflict with Gtk 4.0
    # If the system only has Vte 2.91 (GTK3), this import or require might fail
    # or it might load fine but cause issues later.
    # The typelib for GTK4 Vte is usually named Vte-3.91 or Vte-2.91-gtk4 ? 
    # Actually, on some systems Vte-2.91 is GTK3.
    # We'll rely on the import failing if it tries to load GTK3.
    gi.require_version("Vte", "3.91")
    from gi.repository import Vte
except (ValueError, ImportError) as e:
    print(f"Warning: Vte not available or incompatible: {e}")
    Vte = None

from gi.repository import Gtk, GLib, GObject

class TerminalPanel(Gtk.Box):
    """
    Terminal panel with embedded Vte.Terminal.
    """
    __gtype_name__ = "UltraFilesTerminalPanel"

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("terminal-panel")
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.append(scrolled)
        
        if Vte is not None:
             # Terminal
            self._terminal = Vte.Terminal()
            self._terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.SYSTEM)
            self._terminal.set_mouse_autohide(True)
            scrolled.set_child(self._terminal)
            
            # Spawn shell
            self._spawn_shell(os.path.expanduser("~"))
        else:
            msg = Gtk.Label(label="Terminal integration unavailable.\nMissing 'gir1.2-vte-2.91-gtk4' or 'gir1.2-vte-3.91'.")
            msg.set_wrap(True)
            msg.set_justify(Gtk.Justification.CENTER)
            msg.add_css_class("dim-label")
            msg.set_valign(Gtk.Align.CENTER)
            msg.set_halign(Gtk.Align.CENTER)
            scrolled.set_child(msg)
            self._terminal = None

    def _spawn_shell(self, working_dir: str):
        """Spawn shell in directory"""
        if not self._terminal:
            return

        try:
            shell = os.environ.get("SHELL", "/bin/bash")
            
            self._terminal.spawn_async(
                Vte.PtyFlags.DEFAULT,
                working_dir,
                [shell],
                None,
                GLib.SpawnFlags.DEFAULT,
                None,
                None,
                -1,
                None,
                self._on_spawn_complete,
                None
            )
        except Exception as e:
            print(f"Failed to spawn terminal: {e}")

    def _on_spawn_complete(self, terminal, pid, error, user_data):
        if error:
            print(f"Terminal spawn error: {error}")

    def navigate_to(self, path: str):
        """Change directory"""
        if not self._terminal:
            return

        # Quote path
        cmd = f"cd '{path}'\n"
        self._terminal.feed_child(cmd.encode("utf-8"))

