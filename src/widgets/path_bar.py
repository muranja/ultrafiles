# SPDX-License-Identifier: GPL-3.0-or-later
"""Path bar / breadcrumb navigation widget"""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, GLib, GObject


class PathBar(Gtk.Box):
    """Breadcrumb-style path navigation bar"""

    __gtype_name__ = "UltraFilesPathBar"

    __gsignals__ = {
        "path-selected": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add_css_class("path-bar")

        self._current_path = None
        self._in_edit_mode = False

        # Container for breadcrumbs
        self._crumbs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.append(self._crumbs_box)

        # Path entry (hidden by default)
        self._entry = Gtk.Entry()
        self._entry.set_hexpand(True)
        self._entry.set_visible(False)
        self._entry.connect("activate", self._on_entry_activate)

        # Add key controller for Escape
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_entry_key_pressed)
        self._entry.add_controller(key_controller)

        # Focus controller for focus-out (GTK4 style)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("leave", self._on_entry_focus_leave)
        self._entry.add_controller(focus_controller)

        self.append(self._entry)

        # Click gesture to enter edit mode
        click = Gtk.GestureClick()
        click.connect("pressed", self._on_clicked)
        self._crumbs_box.add_controller(click)

    def set_path(self, path: str):
        """Set the current path and update breadcrumbs"""
        self._current_path = path
        self._update_breadcrumbs()

    def _update_breadcrumbs(self):
        """Rebuild breadcrumb buttons"""
        # Clear existing
        while child := self._crumbs_box.get_first_child():
            self._crumbs_box.remove(child)

        if not self._current_path:
            return

        # Parse path into components
        path = self._current_path
        home = GLib.get_home_dir()

        # Check if path is under home
        if path.startswith(home):
            # Show home icon + relative path
            self._add_crumb("user-home-symbolic", home, is_icon=True)
            relative = path[len(home) :]
            if relative:
                parts = relative.strip("/").split("/")
                current = home
                for part in parts:
                    self._add_separator()
                    current = f"{current}/{part}"
                    self._add_crumb(part, current)
        else:
            # Show full path from root
            if path == "/":
                self._add_crumb("/", "/")
            else:
                parts = path.strip("/").split("/")
                self._add_crumb("/", "/")
                current = ""
                for part in parts:
                    self._add_separator()
                    current = f"{current}/{part}"
                    self._add_crumb(part, current)

    def _add_crumb(self, label: str, path: str, is_icon: bool = False):
        """Add a breadcrumb button"""
        if is_icon:
            btn = Gtk.Button()
            btn.set_child(Gtk.Image.new_from_icon_name(label))
        else:
            btn = Gtk.Button(label=label)

        btn.add_css_class("flat")
        btn.set_can_focus(False)
        btn.crumb_path = path
        btn.connect("clicked", self._on_crumb_clicked)
        self._crumbs_box.append(btn)

    def _add_separator(self):
        """Add a separator between crumbs"""
        sep = Gtk.Label(label="/")
        sep.add_css_class("separator")
        sep.add_css_class("dim-label")
        self._crumbs_box.append(sep)

    def _on_crumb_clicked(self, button):
        """Handle breadcrumb click"""
        if hasattr(button, "crumb_path"):
            self.emit("path-selected", button.crumb_path)

    def _on_clicked(self, gesture, n_press, x, y):
        """Handle click to enter edit mode"""
        if n_press == 1:
            # Check if we clicked on empty space (not a button)
            widget = self._crumbs_box.pick(x, y, Gtk.PickFlags.DEFAULT)
            if widget == self._crumbs_box:
                self._enter_edit_mode()

    def _enter_edit_mode(self):
        """Switch to text entry mode"""
        self._in_edit_mode = True
        self._crumbs_box.set_visible(False)
        self._entry.set_visible(True)
        self._entry.set_text(self._current_path or "")
        self._entry.grab_focus()
        self._entry.select_region(0, -1)

    def _exit_edit_mode(self):
        """Switch back to breadcrumb mode"""
        self._in_edit_mode = False
        self._entry.set_visible(False)
        self._crumbs_box.set_visible(True)

    def _on_entry_activate(self, entry):
        """Handle Enter in entry"""
        path = entry.get_text().strip()
        if path:
            self.emit("path-selected", path)
        self._exit_edit_mode()

    def _on_entry_focus_leave(self, controller):
        """Handle focus leave from entry (GTK4)"""
        self._exit_edit_mode()

    def _on_entry_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press in entry"""
        from gi.repository import Gdk

        if keyval == Gdk.KEY_Escape:
            self._exit_edit_mode()
            return True
        return False
