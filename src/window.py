# SPDX-License-Identifier: GPL-3.0-or-later
"""Main window for UltraFiles"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk, Gdk, GObject

from .widgets.sidebar import Sidebar
from .widgets.path_bar import PathBar
from .widgets.search_bar import SearchBar
from .widgets.terminal_panel import TerminalPanel
from .widgets.file_item import FileItem
from .views.file_list_view import FileListView
from .views.file_grid_view import FileGridView
from .services.directory_loader import DirectoryLoader
from .services.clipboard_service import ClipboardService
from .services.file_operations import FileOperationsService
from .services.search_service import SearchService
from .dialogs.rename_dialog import show_rename_dialog
from .dialogs.batch_rename_dialog import show_batch_rename_dialog
from .dialogs.properties_dialog import show_properties_dialog
from .dialogs.confirm_dialog import show_confirm_dialog, show_new_folder_dialog
from .dialogs.metadata_dialog import show_metadata_dialog
from .viewers.media_viewer import MediaViewer
from .services.recursive_loader import RecursiveLoader


class UltraFilesWindow(Adw.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = "UltraFilesWindow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize settings
        self.settings = Gio.Settings.new("com.ultrafiles.UltraFiles")

        # Navigation history
        self._history = []
        self._history_index = -1
        self._current_path = None

        # Directory loader
        self._loader = DirectoryLoader()

        # Clipboard service
        self._clipboard = ClipboardService()

        # File operations service
        self._file_ops = FileOperationsService()
        self._file_ops.connect("operation-complete", self._on_operation_complete)
        
        # Search service
        self._search_service = SearchService()
        self._search_service.connect("search-result", self._on_search_result)
        self._search_service.connect("search-complete", self._on_search_complete)

        # Git service
        from .services.git_service import GitService
        self._git_service = GitService()
        self._git_service.connect("status-ready", self._on_git_status)

        # Thumbnail service
        from .services.thumbnail_service import ThumbnailService
        self._thumbnail_service = ThumbnailService()
        self._thumbnail_service.connect("thumbnail-ready", self._on_thumbnail_ready)

        # Favorites service
        from .services.favorites_service import FavoritesService
        self._favorites_service = FavoritesService()
        self._favorites_service.connect("changed", self._on_favorites_changed)

        # Tags service
        from .services.tags_service import TagsService
        self._tags_service = TagsService()
        self._tags_service.connect("tags-changed", self._on_tags_changed)

        # Recursive Loader
        self._recursive_loader = RecursiveLoader()

        # File store
        self._file_store = Gio.ListStore.new(FileItem)

        # Set up window
        self._setup_window()
        self._setup_actions()
        self._build_ui()
        
        # Init favorites
        self._on_favorites_changed(self._favorites_service)
        self._on_tags_changed(self._tags_service)

        # Navigate to home directory
        home = GLib.get_home_dir()
        self.navigate_to_path(home)

    def _setup_window(self):
        """Configure window properties"""
        self.set_title("UltraFiles")
        self.set_default_size(
            self.settings.get_int("window-width"),
            self.settings.get_int("window-height"),
        )
        # Set minimum size to prevent Adwaita warnings
        self.set_size_request(360, 400)

        if self.settings.get_boolean("window-maximized"):
            self.maximize()

        # Save window state on close
        self.connect("close-request", self._on_close_request)

    def _setup_actions(self):
        """Set up window actions"""
        actions = [
            ("go-back", self._on_go_back, None),
            ("go-forward", self._on_go_forward, None),
            ("go-up", self._on_go_up, None),
            ("go-home", self._on_go_home, None),
            ("refresh", self._on_refresh, None),
            ("toggle-hidden", self._on_toggle_hidden, None),
            ("search", self._on_search, None),
            ("view-list", self._on_view_list, None),
            ("view-grid", self._on_view_grid, None),
            ("view-columns", self._on_view_columns, None),
            ("new-tab", self._on_new_tab, None),
            ("close-tab", self._on_close_tab, None),
            ("select-all", self._on_select_all, None),
            ("copy", self._on_copy, None),
            ("cut", self._on_cut, None),
            ("paste", self._on_paste, None),
            ("rename", self._on_rename, None),
            ("trash", self._on_trash, None),
            ("delete", self._on_delete, None),
            ("properties", self._on_properties, None),
            ("copy-path", self._on_copy_path, None),
            ("move-to", self._on_move_to, None),
            ("new-folder", self._on_new_folder, None),
            ("toggle-terminal", self._on_toggle_terminal, None),
            ("edit-metadata", self._on_edit_metadata, None),
            ("add-favorite", self._on_add_favorite, None),
            ("remove-favorite", self._on_remove_favorite, None),
            ("toggle-tag", self._on_toggle_tag, GLib.VariantType.new("s")),
            ("zoom-in", self._on_zoom_in, None),
            ("zoom-out", self._on_zoom_out, None),
            ("zoom-reset", self._on_zoom_reset, None),
            ("focus-path-bar", self._on_focus_path_bar, None),
            ("show-all-media", self._on_show_all_media, None),
            ("filter-tag", self._on_filter_tag, GLib.VariantType.new("s")),
            ("group-by", self._on_group_by, GLib.VariantType.new("s")),
        ]

        for name, callback, param_type in actions:
            action = Gio.SimpleAction.new(name, param_type)
            action.connect("activate", callback)
            self.add_action(action)

        # Update action states
        self._update_navigation_actions()

    def _build_ui(self):
        """Build the main UI"""
        # Main layout with toast overlay
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        # Split view for sidebar + content
        self._split_view = Adw.NavigationSplitView()
        self._split_view.set_min_sidebar_width(200)
        self._split_view.set_max_sidebar_width(350)
        self._split_view.set_sidebar_width_fraction(0.2)
        self._toast_overlay.set_child(self._split_view)

        # Create sidebar
        self._sidebar = Sidebar()
        self._sidebar.connect("place-selected", self._on_place_selected)

        sidebar_page = Adw.NavigationPage.new(self._sidebar, "Places")
        self._split_view.set_sidebar(sidebar_page)

        # Create content area
        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # File browser content
        browser_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._content_stack.add_named(browser_box, "browser")

        # Header bar
        header = self._create_header_bar()
        browser_box.append(header)

        # View stack (list/grid views)
        self._view_stack = Gtk.Stack()
        self._view_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._view_stack.set_vexpand(True)

        # Create views
        self._list_view = FileListView(self._file_store)
        self._list_view.connect("file-activated", self._on_file_activated)
        self._list_view.connect("context-menu-requested", self._on_context_menu)
        self._view_stack.add_named(self._list_view, "list")

        self._grid_view = FileGridView(self._file_store)
        self._grid_view.set_thumbnail_service(self._thumbnail_service)
        self._grid_view.set_tags_service(self._tags_service)
        self._grid_view.connect("file-activated", self._on_file_activated)
        self._grid_view.connect("rename-requested", self._on_rename_requested)
        self._grid_view.connect("context-menu-requested", self._on_context_menu)
        self._view_stack.add_named(self._grid_view, "grid")

        # Ctrl+Scroll zoom on the view area
        scroll_ctrl = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
        )
        scroll_ctrl.connect("scroll", self._on_ctrl_scroll)
        self._view_stack.add_controller(scroll_ctrl)

        # Set default view
        default_view = self.settings.get_string("default-view")
        self._view_stack.set_visible_child_name(default_view)

        browser_box.append(self._view_stack)

        # Status bar
        self._status_bar = self._create_status_bar()
        browser_box.append(self._status_bar)

        # Content Split (Browser / Terminal)
        self._content_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        # Start child is the main browser stack
        self._content_paned.set_start_child(self._content_stack)
        self._content_stack.set_vexpand(True) # content expands
        
        # Terminal at bottom
        self._terminal_panel = TerminalPanel()
        self._terminal_panel.set_visible(False)
        self._content_paned.set_end_child(self._terminal_panel)
        self._content_paned.set_position(300) # Default height? Or from bottom?
        # Paned position logic: distance from start or end? Usually from start.
        # If I want bottom 200px, position should be total_height - 200.
        # Dynamic resizing handles it.
        
        content_page = Adw.NavigationPage.new(self._content_paned, "Files")
        self._split_view.set_content(content_page)

        # Add responsive breakpoint
        breakpoint = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-width: 600sp")
        )
        breakpoint.add_setter(self._split_view, "collapsed", True)
        self.add_breakpoint(breakpoint)

    def _create_header_bar(self) -> Adw.HeaderBar:
        """Create the header bar with navigation and controls"""
        header = Adw.HeaderBar()

        # Navigation buttons
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        nav_box.add_css_class("linked")

        self._back_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self._back_btn.set_tooltip_text("Go Back (Alt+Left)")
        self._back_btn.set_action_name("win.go-back")
        nav_box.append(self._back_btn)

        self._forward_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self._forward_btn.set_tooltip_text("Go Forward (Alt+Right)")
        self._forward_btn.set_action_name("win.go-forward")
        nav_box.append(self._forward_btn)

        header.pack_start(nav_box)

        # Up button
        up_btn = Gtk.Button.new_from_icon_name("go-up-symbolic")
        up_btn.set_tooltip_text("Go Up (Alt+Up)")
        up_btn.set_action_name("win.go-up")
        header.pack_start(up_btn)

        # Title Stack (PathBar + SearchBar)
        self._title_stack = Gtk.Stack()
        self._title_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        
        self._path_bar = PathBar()
        self._path_bar.connect("path-selected", self._on_path_selected)
        self._title_stack.add_named(self._path_bar, "path")
        
        self._search_bar = SearchBar()
        self._search_bar.connect("activate", self._on_search_activate)
        self._search_bar.connect("stop-search", self._on_search_stop)
        self._title_stack.add_named(self._search_bar, "search")
        
        self._title_stack.set_visible_child_name("path")
        header.set_title_widget(self._title_stack)

        # Search button
        self._search_btn = Gtk.Button.new_from_icon_name("system-search-symbolic")
        self._search_btn.set_tooltip_text("Search (Ctrl+F)")
        self._search_btn.set_action_name("win.search")
        header.pack_end(self._search_btn)

        # View switcher
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        view_box.add_css_class("linked")

        self._list_btn = Gtk.ToggleButton()
        self._list_btn.set_icon_name("view-list-symbolic")
        self._list_btn.set_tooltip_text("List View (Ctrl+1)")
        self._list_btn.set_active(True)
        self._list_btn.connect("toggled", self._on_view_toggle, "list")
        view_box.append(self._list_btn)

        self._grid_btn = Gtk.ToggleButton()
        self._grid_btn.set_icon_name("view-grid-symbolic")
        self._grid_btn.set_tooltip_text("Grid View (Ctrl+2)")
        self._grid_btn.set_group(self._list_btn)
        self._grid_btn.connect("toggled", self._on_view_toggle, "grid")
        view_box.append(self._grid_btn)

        header.pack_end(view_box)

        # Menu button
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_tooltip_text("Main Menu")
        menu_btn.set_menu_model(self._create_main_menu())
        header.pack_end(menu_btn)

        return header

    def _create_main_menu(self) -> Gio.Menu:
        """Create the main menu"""
        menu = Gio.Menu()

        # View section
        view_section = Gio.Menu()
        view_section.append("Show Hidden Files", "win.toggle-hidden")
        view_section.append("Toggle Terminal (F4)", "win.toggle-terminal")
        view_section.append("Refresh", "win.refresh")
        menu.append_section(None, view_section)

        # File operations
        file_section = Gio.Menu()
        file_section.append("New Folder...", "win.new-folder")
        menu.append_section(None, file_section)

        # App section
        app_section = Gio.Menu()
        app_section.append("Preferences", "app.preferences")
        app_section.append("Keyboard Shortcuts", "win.show-help-overlay")
        app_section.append("About UltraFiles", "app.about")
        menu.append_section(None, app_section)

        return menu

    def _create_status_bar(self) -> Gtk.Box:
        """Create the status bar"""
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.add_css_class("status-bar")

        self._item_count_label = Gtk.Label(label="0 items")
        self._item_count_label.set_xalign(0)
        status_bar.append(self._item_count_label)

        self._selection_label = Gtk.Label()
        self._selection_label.set_xalign(0)
        self._selection_label.set_hexpand(True)
        status_bar.append(self._selection_label)

        self._free_space_label = Gtk.Label()
        self._free_space_label.add_css_class("dim-label")
        status_bar.append(self._free_space_label)

        return status_bar

    def navigate_to_path(self, path: str):
        """Navigate to a directory path"""
        if path == self._current_path:
            return

        gfile = Gio.File.new_for_path(path)
        self._navigate_to_file(gfile, add_to_history=True)

    def _navigate_to_file(self, gfile: Gio.File, add_to_history: bool = True):
        """Navigate to a GFile directory"""
        path = gfile.get_path()

        # Check if directory exists
        if not gfile.query_exists():
            self._show_toast(f"Directory not found: {path}")
            return

        # Add to history
        if add_to_history and path != self._current_path:
            # Truncate forward history
            self._history = self._history[: self._history_index + 1]
            self._history.append(path)
            self._history_index = len(self._history) - 1

        self._current_path = path

        # Update UI
        self._path_bar.set_path(path)
        self._update_navigation_actions()
        
        # Update Terminal
        if self._terminal_panel.get_visible():
            self._terminal_panel.navigate_to(path)

        # Load directory contents
        self._load_directory(gfile)

    def _load_directory(self, gfile: Gio.File):
        """Load directory contents asynchronously"""
        # Cancel stale thumbnail jobs from the previous directory
        self._thumbnail_service.cancel_pending()

        # Clear current files and cached media list
        self._file_store.remove_all()
        self._media_items: list[FileItem] = []

        show_hidden = self.settings.get_boolean("show-hidden-files")

        def on_files_loaded(items, error):
            if error:
                self._show_toast(f"Error loading directory: {error.message}")
                return

            if items is None:
                # Loading complete — build media cache and update UI
                self._media_items = [
                    self._file_store.get_item(i)
                    for i in range(self._file_store.get_n_items())
                    if self._file_store.get_item(i).is_media()
                ]
                self._update_status_bar()

                # Fetch git status once at completion
                if gfile.query_exists() and not gfile.get_uri().startswith("search:"):
                    self._git_service.fetch_status(gfile.get_path())
                return

            # Filter hidden files, then batch-add via splice (single sort model update)
            filtered = [item for item in items if show_hidden or not item.is_hidden]
            if filtered:
                pos = self._file_store.get_n_items()
                self._file_store.splice(pos, 0, filtered)

            # Light update — just item count, no filesystem query
            count = self._file_store.get_n_items()
            self._item_count_label.set_label(f"{count} items")

        self._loader.load_directory(gfile, on_files_loaded)

    def _update_navigation_actions(self):
        """Update navigation action sensitivity"""
        can_go_back = self._history_index > 0
        can_go_forward = self._history_index < len(self._history) - 1
        can_go_up = self._current_path and self._current_path != "/"

        self.lookup_action("go-back").set_enabled(can_go_back)
        self.lookup_action("go-forward").set_enabled(can_go_forward)
        self.lookup_action("go-up").set_enabled(can_go_up)

    def _update_status_bar(self):
        """Update status bar information"""
        count = self._file_store.get_n_items()
        self._item_count_label.set_label(f"{count} items")

        # Get free space
        if self._current_path:
            try:
                gfile = Gio.File.new_for_path(self._current_path)
                info = gfile.query_filesystem_info(
                    Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE, None
                )
                free = info.get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE)
                self._free_space_label.set_label(f"{GLib.format_size(free)} free")
            except Exception:
                self._free_space_label.set_label("")

    def _show_toast(self, message: str, action_label: str = None, action_callback=None):
        """Show a toast notification"""
        toast = Adw.Toast.new(message)
        toast.set_timeout(5)

        if action_label and action_callback:
            toast.set_button_label(action_label)
            toast.connect("button-clicked", lambda t: action_callback())

        self._toast_overlay.add_toast(toast)

    def _get_selected_files(self) -> list:
        """Get list of selected file paths"""
        current_view = self._view_stack.get_visible_child()
        if hasattr(current_view, "get_selected_items"):
            items = current_view.get_selected_items()
            return [item.path for item in items if item.path]
        return []

    def _on_operation_complete(self, service, message: str, success: bool):
        """Handle file operation completion"""
        self._show_toast(message)
        if success and self._current_path:
            self._on_refresh(None, None)

    # --- Event Handlers ---

    def _on_close_request(self, window):
        """Save window state on close"""
        if not self.is_maximized():
            width, height = self.get_default_size()
            self.settings.set_int("window-width", width)
            self.settings.set_int("window-height", height)

        self.settings.set_boolean("window-maximized", self.is_maximized())
        return False

    def _on_place_selected(self, sidebar, path: str):
        """Handle place selection in sidebar"""
        if path.startswith("file://"):
            gfile = Gio.File.new_for_uri(path)
        else:
            gfile = Gio.File.new_for_path(path)
        self._navigate_to_file(gfile)

    def _on_path_selected(self, path_bar, path: str):
        """Handle path selection from path bar"""
        self.navigate_to_path(path)

    def _on_git_status(self, service, directory, status_map):
        """Handle git status update"""
        # Only update if we are still viewing that directory
        if not self._current_path or self._current_path != directory:
            return
            
        # Iterate store and update items
        for i in range(self._file_store.get_n_items()):
            item = self._file_store.get_item(i)
            # Match by relative path or filename?
            # Git status usually returns relative paths to repo root or cwd.
            # GitService used cwd=directory. So relative to directory.
            # FileItem has name.
            if item.display_name in status_map:
                item.git_status = status_map[item.display_name]

    def _on_thumbnail_ready(self, service, uri, path):
        """Handle thumbnail ready"""
        # Linear search for now (Limit items usually < 1000)
        # Optimization: Map URI to items if needed
        for i in range(self._file_store.get_n_items()):
            item = self._file_store.get_item(i)
            if item.uri == uri:
                item.set_thumbnail_path(path)
                return # Can return if unique URI
    
    def _on_file_activated(self, view, file_item: FileItem):
        """Handle file/folder activation (double-click/enter)"""
        if file_item.is_directory:
            self._navigate_to_file(file_item.gfile)
        elif file_item.is_media():
            # Use cached media list — find the start index
            media_items = self._media_items if hasattr(self, '_media_items') else []
            if not media_items:
                media_items = [file_item]
            start_index = 0
            for i, item in enumerate(media_items):
                if item.path == file_item.path:
                    start_index = i
                    break

            self._open_media_viewer(media_items, start_index)
        else:
            # Open file with default application
            try:
                Gio.AppInfo.launch_default_for_uri(file_item.gfile.get_uri(), None)
            except Exception as e:
                self._show_toast(f"Could not open file: {e}")

    def _open_media_viewer(self, items, start_index):
        """Open the integrated media viewer"""
        # Remove existing viewer if any
        if hasattr(self, "_media_viewer"):
            self._media_viewer.cleanup()
            self._content_stack.remove(self._media_viewer)

        self._media_viewer = MediaViewer(items, start_index)
        self._media_viewer.connect("close-viewer", self._close_media_viewer)

        self._content_stack.add_named(self._media_viewer, "media-viewer")
        self._content_stack.set_visible_child_name("media-viewer")

        # Collapse sidebar and show content for immersive viewing
        self._split_view.set_collapsed(True)
        self._split_view.set_show_content(True)

    def _close_media_viewer(self, widget):
        """Close media viewer and return to browser"""
        self._content_stack.set_visible_child_name("browser")

        # Restore split view
        self._split_view.set_show_content(False)
        width = self.get_default_size()[0]
        if width > 600:
            self._split_view.set_collapsed(False)

        # Clean up viewer — stop playback, release resources
        if hasattr(self, "_media_viewer"):
            self._media_viewer.cleanup()
            self._content_stack.remove(self._media_viewer)
            del self._media_viewer

    def _on_context_menu(self, view, x: float, y: float, file_item: FileItem):
        """Show context menu for file"""
        menu = self._create_context_menu(file_item)
        popover = Gtk.PopoverMenu.new_from_model(menu)
        popover.set_parent(view)
        popover.set_pointing_to(Gdk.Rectangle(int(x), int(y), 1, 1))
        popover.popup()

    def _create_context_menu(self, file_item: FileItem = None) -> Gio.Menu:
        """Create context menu for file operations"""
        menu = Gio.Menu()

        if file_item:
            # Open section
            open_section = Gio.Menu()
            open_section.append("Open", "win.open")
            open_section.append("Open With...", "win.open-with")
            if file_item.is_directory:
                open_section.append("Show All Media", "win.show-all-media")
            menu.append_section(None, open_section)

            # Edit section
            edit_section = Gio.Menu()
            edit_section.append("Cut", "win.cut")
            edit_section.append("Copy", "win.copy")
            edit_section.append("Copy Path", "win.copy-path")
            menu.append_section(None, edit_section)

            # Metadata (Audio only)
            if file_item.is_audio():
                meta_section = Gio.Menu()
                meta_section.append("Edit Metadata...", "win.edit-metadata")
                menu.append_section(None, meta_section)

            # Favorites
            fav_section = Gio.Menu()
            if self._favorites_service.is_favorite(file_item.uri):
                fav_section.append("Remove from Favorites", "win.remove-favorite")
            else:
                fav_section.append("Add to Favorites", "win.add-favorite")
            menu.append_section(None, fav_section)

            # Tags
            tags_menu = Gio.Menu()
            current_tags = self._tags_service.get_tags_for_file(file_item.uri)
            for tag in self._tags_service.get_available_tags():
                name = tag["name"]
                label = f"✓ {name}" if name in current_tags else name
                tags_menu.append(label, f"win.toggle-tag('{name}')")
            menu.append_submenu("Tags", tags_menu)

            # Move section
            move_section = Gio.Menu()
            move_section.append("Move to...", "win.move-to")
            move_section.append("Rename", "win.rename")
            move_section.append("Move to Trash", "win.trash")
            menu.append_section(None, move_section)

            # Properties
            props_section = Gio.Menu()
            props_section.append("Properties", "win.properties")
            menu.append_section(None, props_section)
        else:
            # Empty area context menu
            create_section = Gio.Menu()
            create_section.append("New Folder...", "win.new-folder")
            create_section.append("Paste", "win.paste")
            menu.append_section(None, create_section)

            view_section = Gio.Menu()
            view_section.append("Refresh", "win.refresh")
            view_section.append("Show Hidden Files", "win.toggle-hidden")
            
            # Group By Submenu
            group_menu = Gio.Menu()
            group_menu.append("None", "win.group-by('none')")
            group_menu.append("Folder", "win.group-by('folder')")
            group_menu.append("Tag", "win.group-by('tag')")
            view_section.append_submenu("Group By", group_menu)

            # Filter By Tag Submenu
            filter_menu = Gio.Menu()
            filter_menu.append("All", "win.filter-tag('')")
            for tag in self._tags_service.get_available_tags():
                name = tag["name"]
                filter_menu.append(name, f"win.filter-tag('{name}')")
            view_section.append_submenu("Filter by Tag", filter_menu)

            menu.append_section(None, view_section)

        return menu

    def _on_view_toggle(self, button, view_name: str):
        """Handle view toggle button"""
        if button.get_active():
            self._view_stack.set_visible_child_name(view_name)
            self.settings.set_string("default-view", view_name)

    # --- Action Handlers ---

    def _on_go_back(self, action, param):
        if self._history_index > 0:
            self._history_index -= 1
            path = self._history[self._history_index]
            gfile = Gio.File.new_for_path(path)
            self._navigate_to_file(gfile, add_to_history=False)

    def _on_go_forward(self, action, param):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            path = self._history[self._history_index]
            gfile = Gio.File.new_for_path(path)
            self._navigate_to_file(gfile, add_to_history=False)

    def _on_go_up(self, action, param):
        if self._current_path and self._current_path != "/":
            parent = Gio.File.new_for_path(self._current_path).get_parent()
            if parent:
                self._navigate_to_file(parent)

    def _on_go_home(self, action, param):
        self.navigate_to_path(GLib.get_home_dir())

    def _on_refresh(self, action, param):
        if self._current_path:
            gfile = Gio.File.new_for_path(self._current_path)
            self._load_directory(gfile)

    def _on_toggle_hidden(self, action, param):
        current = self.settings.get_boolean("show-hidden-files")
        self.settings.set_boolean("show-hidden-files", not current)
        self._on_refresh(None, None)

        status = "shown" if not current else "hidden"
        self._show_toast(f"Hidden files {status}")

    def _on_search(self, action, param):
        # Toggle search mode
        if self._title_stack.get_visible_child_name() == "search":
             self._on_search_stop(self._search_bar)
        else:
             self._title_stack.set_visible_child_name("search")
             self._search_bar.grab_focus()
             
    def _on_search_activate(self, entry):
        query = entry.get_text()
        self._start_search(query)
        
    def _on_search_stop(self, entry):
        entry.set_text("")
        self._title_stack.set_visible_child_name("path")
        # Restore view if needed?
        if self._current_path:
             self._on_refresh(None, None)
             self._path_bar.set_path(self._current_path)
        
    def _start_search(self, query):
        if not query:
            return
            
        self._show_toast(f"Searching for '{query}'...")
        self._file_store.remove_all()
        # Navigate to "Search Results" virtual path?
        self._path_bar.set_path(f"Search: {query}")
        self._current_path = None # Virtual
        
        # Start search in current directory (or home if none)
        # We need the directory to search IN.
        # Ideally search starts from where we were.
        # But I just cleared _current_path.
        # I should save it.
        search_dir = self._history[self._history_index] if self._history else GLib.get_home_dir()
        
        gfile = Gio.File.new_for_path(search_dir)
        self._search_service.search(gfile, query)
        
    def _on_search_result(self, service, file: Gio.File):
        # Create item via loader logic or direct
        # Subprocess search returns file paths.
        # We need FileAttributes.
        # We can query them async or just create basic item.
        # Querying invalidates async speed if we wait.
        # But FileItem needs info.
        # Let's verify file exists and get info.
        
        # Optimization: Batch queries?
        # For now, just create item with basic info.
        try:
             info = file.query_info(DirectoryLoader.ATTRIBUTES, Gio.FileQueryInfoFlags.NONE, None)
             item = FileItem(info, file.get_parent())
             self._file_store.append(item)
        except Exception:
             pass

    def _on_search_complete(self, service, success, message):
        if not success:
            self._show_toast(f"Search failed: {message}")
        else:
            count = self._file_store.get_n_items()
            self._show_toast(f"Found {count} matches")
            self._update_status_bar()

    def _on_show_all_media(self, action, param):
        """Show all media in selected folder recursively"""
        selected = self._get_selected_files()
        if not selected:
            return
            
        path = selected[0] # Just take first
        gfile = Gio.File.new_for_path(path)
        
        self._show_toast(f"Scanning for media in {gfile.get_basename()}...")
        
        # Switch to Grid View
        self._grid_btn.set_active(True)
        
        # Virtual navigation
        self._path_bar.set_path(f"Media: {gfile.get_basename()}")
        self._current_path = None 
        self._file_store.remove_all()
        self._item_count_label.set_label("Scanning...")
        
        def on_loaded(items, error):
            if error:
                self._show_toast(f"Scan failed: {error.message}")
                return
                
            if items is None:
                count = self._file_store.get_n_items()
                self._show_toast(f"Found {count} media files")
                self._update_status_bar()
                return
                
            # Add items
            if items:
                self._file_store.splice(self._file_store.get_n_items(), 0, items)
                self._update_status_bar() # incremental update

        self._recursive_loader.load_recursive(gfile, on_loaded, file_filter="media")

    def _on_group_by(self, action, param):
        mode = param.get_string()
        if mode == 'none': mode = None
        self._grid_view.set_group_by(mode)
        
    def _on_filter_tag(self, action, param):
        tag = param.get_string()
        if not tag: tag = None
        self._grid_view.set_filter_by_tag(tag)

    def _on_view_list(self, action, param):
        self._list_btn.set_active(True)

    def _on_view_grid(self, action, param):
        self._grid_btn.set_active(True)

    def _on_view_columns(self, action, param):
        # TODO: Implement column view
        self._show_toast("Column view coming soon!")

    def _on_zoom_in(self, action, param):
        self._grid_view.zoom_in()

    def _on_zoom_out(self, action, param):
        self._grid_view.zoom_out()

    def _on_zoom_reset(self, action, param):
        self._grid_view.zoom_reset()

    def _on_focus_path_bar(self, action, param):
        """Focus the path bar for keyboard-driven navigation."""
        self._path_bar.grab_focus()

    def _on_ctrl_scroll(self, controller, dx, dy):
        """Handle Ctrl+Scroll for zoom."""
        # Only zoom when Ctrl is held
        from gi.repository import Gdk
        seat = self.get_display().get_default_seat()
        keyboard = seat.get_keyboard() if seat else None
        mods = controller.get_current_event_state()
        if not (mods & Gdk.ModifierType.CONTROL_MASK):
            return False

        if dy < 0:
            self._grid_view.zoom_in()
        elif dy > 0:
            self._grid_view.zoom_out()
        return True

    def _on_new_tab(self, action, param):
        # TODO: Implement tabs
        self._show_toast("Tabs coming soon!")

    def _on_close_tab(self, action, param):
        pass

    def _on_select_all(self, action, param):
        current_view = self._view_stack.get_visible_child()
        if hasattr(current_view, "select_all"):
            current_view.select_all()

    def _on_copy(self, action, param):
        selected = self._get_selected_files()
        if selected:
            self._clipboard.copy(selected)
            self._show_toast(
                f"Copied {len(selected)} item{'s' if len(selected) > 1 else ''}"
            )
        else:
            self._show_toast("No files selected")

    def _on_cut(self, action, param):
        selected = self._get_selected_files()
        if selected:
            self._clipboard.cut(selected)
            self._show_toast(
                f"Cut {len(selected)} item{'s' if len(selected) > 1 else ''}"
            )
        else:
            self._show_toast("No files selected")

    def _on_paste(self, action, param):
        if not self._current_path:
            return

        files, operation = self._clipboard.get_files()
        if not files:
            self._show_toast("Nothing to paste")
            return

        if operation.value == "cut":
            self._file_ops.move_files(files, self._current_path)
        else:
            self._file_ops.copy_files(files, self._current_path)

    def _get_selected_items(self):
        """Get selected FileItem objects"""
        view_name = self._view_stack.get_visible_child_name()
        if view_name == "list":
            return self._list_view.get_selected_items()
        elif view_name == "grid":
            return self._grid_view.get_selected_items()
        return []

    def _on_rename(self, action, param):
        selected_items = self._get_selected_items()
        if not selected_items:
            self._show_toast("No files selected")
            return
            
        if len(selected_items) > 1:
            # Batch rename
            def on_batch_rename(results):
                if results:
                    for path, new_name in results:
                         self._file_ops.rename_file(path, new_name)
                    self._show_toast(f"Renamed {len(results)} files")

            show_batch_rename_dialog(self, selected_items, on_batch_rename)
        else:
            # Single rename
            file_item = selected_items[0]
            current_name = file_item.display_name
            file_path = file_item.path
            
            def on_rename(new_name):
                if new_name:
                    self._file_ops.rename_file(file_path, new_name)

            show_rename_dialog(self, current_name, on_rename)

    
    def _on_tags_changed(self, service):
        """Handle tags change"""
        for i in range(self._file_store.get_n_items()):
            item = self._file_store.get_item(i)
            item.tags = service.get_tags_for_file(item.uri)

    def _on_favorites_changed(self, service):
        """Handle favorites change"""
        favorites = service.get_favorites()
        if hasattr(self, "_sidebar"):
             self._sidebar.update_favorites(favorites)
             
        # Update current items
        for i in range(self._file_store.get_n_items()):
            item = self._file_store.get_item(i)
            item.is_favorite = service.is_favorite(item.uri)

    def _on_rename_requested(self, view, file_item, new_name):
        """Handle inline rename request"""
        if file_item and new_name:
            self._file_ops.rename_file(file_item.path, new_name)

    def _on_add_favorite(self, action, param):
        items = self._get_selected_items()
        for item in items:
            self._favorites_service.add_favorite(item.uri)
            
    def _on_remove_favorite(self, action, param):
        items = self._get_selected_items()
        for item in items:
            self._favorites_service.remove_favorite(item.uri)

    def _on_toggle_tag(self, action, param):
        tag = param.get_string()
        items = self._get_selected_items()
        for item in items:
            self._tags_service.toggle_tag(item.uri, tag)

    def _on_trash(self, action, param):
        selected = self._get_selected_files()
        if selected:
            self._file_ops.trash_files(selected)
        else:
            self._show_toast("No files selected")

    def _on_delete(self, action, param):
        selected = self._get_selected_files()
        if not selected:
            self._show_toast("No files selected")
            return

        def on_confirm(confirmed):
            if confirmed:
                self._file_ops.delete_files(selected)

        count = len(selected)
        msg = f"Permanently delete {count} item{'s' if count != 1 else ''}?"
        show_confirm_dialog(self, "Delete Files", msg, "Delete", on_confirm)

    def _on_properties(self, action, param):
        selected = self._get_selected_files()
        if len(selected) != 1:
            self._show_toast("Select exactly one file to view properties")
            return

        # We need the FileItem, not just the path
        # Find it in the store
        # This is a bit inefficient, but safe
        path = selected[0]
        found_item = None
        for i in range(self._file_store.get_n_items()):
            item = self._file_store.get_item(i)
            if item.path == path:
                found_item = item
                break

        if found_item:
            show_properties_dialog(self, found_item)
        else:
            self._show_toast("Could not find file info")

    def _on_copy_path(self, action, param):
        """Copy file path to clipboard"""
        current_view = self._view_stack.get_visible_child()
        if hasattr(current_view, "get_selected_items"):
            items = current_view.get_selected_items()
            if items:
                paths = "\n".join(item.path for item in items)
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(paths)
                self._show_toast("Path copied to clipboard")

    def _on_move_to(self, action, param):
        selected = self._get_selected_files()
        if not selected:
            self._show_toast("Select files to move")
            return

        dialog = Gtk.FileDialog()
        dialog.set_title("Move to...")

        def on_folder_selected(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    dest_path = folder.get_path()
                    if dest_path:
                        self._file_ops.move_files(selected, dest_path)
            except GLib.Error as e:
                pass  # Cancelled or error

        dialog.select_folder(self, None, on_folder_selected)

    def _on_new_folder(self, action, param):
        if not self._current_path:
            return

        def on_create(name):
            if name:
                self._file_ops.create_folder(self._current_path, name)

        show_new_folder_dialog(self, on_create)

    def _on_toggle_terminal(self, action, param):
        is_visible = self._terminal_panel.get_visible()
        self._terminal_panel.set_visible(not is_visible)
        
        if not is_visible and self._current_path:
            self._terminal_panel.navigate_to(self._current_path)

    def _on_edit_metadata(self, action, param):
        selected = self._get_selected_files()
        if len(selected) != 1:
            self._show_toast("Select exactly one file")
            return
            
        def on_save(success):
            if success:
                self._show_toast("Metadata saved")
                self._on_refresh(None, None)
            else:
                self._show_toast("Failed to save metadata")
                
        show_metadata_dialog(self, selected[0], on_save)
