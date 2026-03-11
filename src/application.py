# SPDX-License-Identifier: GPL-3.0-or-later
"""UltraFiles Application class"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk, Gdk

from .window import UltraFilesWindow


class UltraFilesApplication(Adw.Application):
    """The main UltraFiles application"""

    def __init__(self, version: str = "0.1.0"):
        super().__init__(
            application_id="com.ultrafiles.UltraFiles",
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self.version = version
        self.set_resource_base_path("/com/ultrafiles/UltraFiles")

    def do_startup(self):
        """Called when the application starts"""
        Adw.Application.do_startup(self)
        self._load_css()
        self._setup_actions()
        self._setup_accels()

    def do_activate(self):
        """Called when the application is activated"""
        win = self.props.active_window
        if not win:
            win = UltraFilesWindow(application=self)
        win.present()

    def do_open(self, files, n_files, hint):
        """Handle opening directories from command line or file manager"""
        self.do_activate()
        if files:
            # Navigate to the first directory
            path = files[0].get_path()
            if path:
                win = self.props.active_window
                win.navigate_to_path(path)

    def _load_css(self):
        """Load custom CSS stylesheet"""
        import os

        css_provider = Gtk.CssProvider()
        resource_path = "/com/ultrafiles/UltraFiles/style.css"

        # Check if the GResource is registered (packaged builds)
        resource_available = False
        try:
            Gio.resources_lookup_data(resource_path, Gio.ResourceLookupFlags.NONE)
            resource_available = True
        except GLib.Error:
            pass

        if resource_available:
            css_provider.load_from_resource(resource_path)
        else:
            # Running from source — load the CSS file directly
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            css_path = os.path.join(project_root, "data", "resources", "style.css")
            if os.path.exists(css_path):
                css_provider.load_from_path(css_path)
            else:
                print(f"Warning: CSS file not found at {css_path}")
                return

        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _setup_actions(self):
        """Set up application actions"""
        actions = [
            ("quit", self._on_quit, None),
            ("new-window", self._on_new_window, None),
            ("about", self._on_about, None),
            ("preferences", self._on_preferences, None),
        ]

        for name, callback, param_type in actions:
            action = Gio.SimpleAction.new(name, param_type)
            action.connect("activate", callback)
            self.add_action(action)

    def _setup_accels(self):
        """Set up keyboard accelerators"""
        accels = {
            "app.quit": ["<Control>q"],
            "app.new-window": ["<Control>n"],
            "app.preferences": ["<Control>comma"],
            "win.new-tab": ["<Control>t"],
            "win.close-tab": ["<Control>w"],
            "win.go-back": ["<Alt>Left"],
            "win.go-forward": ["<Alt>Right"],
            "win.go-up": ["<Alt>Up", "BackSpace"],
            "win.go-home": ["<Alt>Home"],
            "win.refresh": ["F5", "<Control>r"],
            "win.toggle-hidden": ["<Control>h"],
            "win.search": ["<Control>f"],
            "win.select-all": ["<Control>a"],
            "win.copy": ["<Control>c"],
            "win.cut": ["<Control>x"],
            "win.paste": ["<Control>v"],
            "win.rename": ["F2"],
            "win.trash": ["Delete"],
            "win.delete": ["<Shift>Delete"],
            "win.properties": ["<Alt>Return"],
            "win.view-list": ["<Control>1"],
            "win.view-grid": ["<Control>2"],
            "win.view-columns": ["<Control>3"],
            "win.zoom-in": ["<Control>plus", "<Control>equal"],
            "win.zoom-out": ["<Control>minus"],
            "win.zoom-reset": ["<Control>0"],
            "win.focus-path-bar": ["<Control>l"],
            "win.new-folder": ["<Control><Shift>n"],
            "win.toggle-terminal": ["F4"],
        }

        for action, shortcuts in accels.items():
            self.set_accels_for_action(action, shortcuts)

    def _on_quit(self, action, param):
        """Quit the application"""
        self.quit()

    def _on_new_window(self, action, param):
        """Create a new window"""
        win = UltraFilesWindow(application=self)
        win.present()

    def _on_about(self, action, param):
        """Show the about dialog"""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="UltraFiles",
            application_icon="system-file-manager",
            developer_name="UltraFiles Team",
            version=self.version,
            website="https://github.com/ultrafiles/ultrafiles",
            issue_url="https://github.com/ultrafiles/ultrafiles/issues",
            license_type=Gtk.License.MIT_X11,
            copyright="Copyright 2026 UltraFiles Team",
            developers=["UltraFiles Team"],
            comments="A modern, lightweight file manager for Linux",
        )
        about.present()

    def _on_preferences(self, action, param):
        """Show the preferences window"""
        # TODO: Implement preferences window
        pass
