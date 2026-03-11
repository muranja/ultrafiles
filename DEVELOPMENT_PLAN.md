# UltraFiles - Development Plan & Progress

## Project Overview

UltraFiles is a modern, lightweight file manager for Linux built with **GTK4 + LibAdwaita + Python**. It aims to provide a better-than-Windows-11 file manager experience with native Linux integration, low memory usage (~30-80 MB), and advanced features like video preview on hover.

### Design Philosophy
- **Lightweight**: Native GTK4, no web technologies
- **Modern**: Clean, dark-themed UI with cyan accent color
- **Feature-Rich**: Integrated media viewers, tabs, dual pane
- **Performant**: Async operations, virtualized lists for large directories

### Color Scheme
- **Background**: `#0a0a0a` (Nearly black)
- **Surface**: `#121212` (Dark gray)
- **Accent**: `#00d4ff` (Cyan - modern and vibrant)
- **Text**: `#f0f0f0` (Off-white)
- **Dim Text**: `#808080` (Gray)

---

## Progress Overview

| Phase | Status | Completion |
|-------|---------|------------|
| Phase 1: Foundation | ✅ Complete | 100% |
| Phase 2: File Operations | 🚧 In Progress | 10% |
| Phase 3: Thumbnails & Preview | ⏳ Planned | 0% |
| Phase 4: Media Viewers | ⏳ Planned | 0% |
| Phase 5: Advanced Features | ⏳ Planned | 0% |
| Phase 6: Cloud Integration | ⏳ Planned | 0% |

---

## Phase 1: Foundation ✅

**Goal**: Core application structure and basic file browsing

### Completed Tasks ✅

- [x] **Project Structure** (1/1)
  - [x] Meson build system setup
  - [x] Directory structure created (src/, data/, po/)
  - [x] Development runner script (run.py)

- [x] **Core Application** (1/1)
  - [x] Adw.Application subclass
  - [x] GSettings integration for preferences
  - [x] Action system with keyboard accelerators
  - [x] About dialog

- [x] **Main Window** (1/1)
  - [x] Adw.ApplicationWindow with NavigationSplitView
  - [x] Header bar with navigation controls
  - [x] Window state persistence (size, maximized)
  - [x] Responsive design (sidebar collapse on narrow screens)

- [x] **Sidebar** (1/1)
  - [x] Places list (Home, Documents, Downloads, Trash, etc.)
  - [x] Devices section (Computer, mounted volumes)
  - [x] Bookmarks section (with GSettings persistence)
  - [x] Section headers and styling

- [x] **Path Bar** (1/1)
  - [x] Breadcrumb navigation
  - [x] Edit mode (click to type path)
  - [x] Home path abbreviation (show ~/...)
  - [x] Keyboard navigation (Escape to exit edit mode)

- [x] **File Views** (2/2)
  - [x] List View (details with name, type, size, date)
  - [x] Grid View (icon/thumbnail mode)
  - [x] View switching (buttons + keyboard)
  - [x] MultiSelection support

- [x] **Data Models** (1/1)
  - [x] FileItem GObject wrapper
  - [x] DirectoryLoader with async enumeration (batched)
  - [x] Custom sorter (folders first, configurable field)

- [x] **Styling** (1/1)
  - [x] Dark theme with cyan accent
  - [x] Custom CSS for all components
  - [x] Animations (fade-in, hover effects)
  - [x] GResource integration

- [x] **Navigation** (1/1)
  - [x] Back/Forward history
  - [x] Up directory
  - [x] Home button
  - [x] Path bar navigation
  - [x] Refresh

- [x] **Settings** (1/1)
  - [x] GSettings schema with all preferences
  - [x] Default view mode
  - [x] Show hidden files
  - [x] Sort options (by, ascending, folders first)
  - [x] Window state persistence

### Current Features
- Browse file system with list or grid view
- Navigate with breadcrumbs, back/forward, up buttons
- Toggle hidden files (Ctrl+H)
- Switch between list and grid view
- Basic file activation (open with default app)
- Context menu structure (not fully functional yet)
- Keyboard shortcuts registered
- Dark theme with cyan accents

---

## Phase 2: File Operations 🚧

**Goal**: Complete file management functionality (copy, cut, paste, delete, rename)

### Tasks

#### 2.1 Clipboard Service (0/1)
- [ ] ClipboardService class
  - [ ] Store copied files with operation type (copy/cut)
  - [ ] Support both internal and system clipboard
  - [ ] Handle file list serialization
  - [ ] Get/paste from clipboard

#### 2.2 File Operations (0/5)
- [ ] Copy files/folders
  - [ ] Single file copy with progress
  - [ ] Batch copy with queue
  - [ ] Overwrite confirmation dialog
  - [ ] Error handling (permissions, disk space)
  - [ ] Progress dialog

- [ ] Cut files/folders
  - [ ] Mark files for move
  - [ ] Visual indication in UI
  - [ ] Paste as move operation

- [ ] Paste from clipboard
  - [ ] Detect operation type (copy/move)
  - [ ] Execute with progress
  - [ ] Handle same-destination paste

- [ ] Delete/Trash
  - [ ] Move to trash (Gio.File.trash_async)
  - [ ] Permanent delete with confirmation
  - [ ] Undo functionality for trash

- [ ] Rename
  - [ ] Rename dialog with validation
  - [ ] Handle name conflicts
  - [ ] Error feedback

#### 2.3 Context Menu (1/2)
- [x] Context menu structure
- [ ] Connect all actions to handlers
  - [ ] Open with default application
  - [ ] Open with... (application picker)
  - [ ] Copy/Cut/Paste
  - [ ] Copy Path to clipboard
  - [ ] Move to... (folder picker)
  - [ ] Rename
  - [ ] Delete/Trash
  - [ ] Properties

#### 2.4 Drag & Drop (0/1)
- [ ] Native drag support
  - [ ] Drag start from file list
  - [ ] Drop handling
  - [ ] Visual feedback during drag
  - [ ] Inter-window drag & drop

#### 2.5 Properties Dialog (0/1)
- [ ] File properties dialog
  - [ ] Name, path, type
  - [ ] Size (with calculation for folders)
  - [ ] Permissions (read/write/execute)
  - [ ] Modification, access, creation times
  - [ ] MIME type
  - [ ] Open with application

---

## Phase 3: Thumbnails & Video Preview ⏳

**Goal**: Generate and display thumbnails for images and videos, with video preview on hover

### Tasks

#### 3.1 Thumbnail Service (0/1)
- [ ] ThumbnailService class
  - [ ] Check XDG thumbnail cache
  - [ ] Load cached thumbnails
  - [ ] Queue thumbnail generation
  - [ ] Background threading for generation
  - [ ] Thumbnail size variants (normal/large)

#### 3.2 Image Thumbnails (0/1)
- [ ] Generate from image files
  - [ ] GdkPixbuf.Pixbuf.new_from_file_at_scale()
  - [ ] Support formats (JPEG, PNG, WEBP, GIF, SVG)
  - [ ] Cache in ~/.cache/thumbnails/ultrafiles/
  - [ ] Error handling for corrupt images

#### 3.3 Video Thumbnails (0/1)
- [ ] Generate from video files
  - [ ] GStreamer pipeline for frame extraction
  - [ ] Extract frame at 1 second
  - [ ] Scale to thumbnail size
  - [ ] Fallback to ffmpegthumbnailer if available
  - [ ] Cache results

#### 3.4 PDF Thumbnails (0/1)
- [ ] Generate from PDF files
  - [ ] Poppler page.render() to Cairo
  - [ ] Convert to Pixbuf
  - [ ] First page thumbnail
  - [ ] Cache results

#### 3.5 Grid View Thumbnails (0/1)
- [ ] Display thumbnails in grid
  - [ ] Async loading in grid items
  - [ ] Fallback to icon while loading
  - [ ] Thumbnail refresh on file change

#### 3.6 Video Preview on Hover (0/1)
- [ ] VideoPreviewWidget
  - [ ] Hover detection with delay (300ms)
  - [ ] Gtk.MediaFile for playback
  - [ ] Muted by default
  - [ ] Loop playback
  - [ ] Smooth fade transition
  - [ ] Stop on mouse leave
  - [ ] Performance: only load visible thumbnails

---

## Phase 4: Media Viewers ⏳

**Goal**: Integrated viewers for images, PDFs, videos, and text files

### Tasks

#### 4.1 Image Viewer (0/1)
- [ ] ImageViewerWindow
  - [ ] Fullscreen mode
  - [ ] Zoom in/out (scroll, buttons)
  - [ ] Pan (drag)
  - [ ] Rotate (90° steps)
  - [ ] Fit to screen/width/height
  - [ ] Navigation (next/previous)

#### 4.2 Image Slideshow (0/1)
- [ ] Slideshow functionality
  - [ ] Auto-advance with configurable interval
  - [ ] Play/pause
  - [ ] Manual navigation
  - [ ] Progress indicator
  - [ ] Fade transitions

#### 4.3 PDF Viewer (0/1)
- [ ] PDFViewerWindow
  - [ ] Poppler.Document integration
  - [ ] Page navigation (first/prev/next/last)
  - [ ] Jump to page
  - [ ] Zoom (in/out/fit)
  - [ ] Scroll rendering
  - [ ] Text search
  - [ ] Page thumbnails

#### 4.4 Video Player (0/1)
- [ ] VideoPlayerWindow
  - [ ] Gtk.Video or Gtk.MediaFile
  - [ ] Custom controls (play/pause, seek, volume)
  - [ ] Progress bar with seeking
  - [ ] Time display (current/total)
  - [ ] Fullscreen
  - [ ] Subtitle support
  - [ ] Playback speed control

#### 4.5 Text Viewer (0/1)
- [ ] TextViewerWindow
  - [ ] Load text files with encoding detection
  - [ ] Syntax highlighting (Pygments)
  - [ ] Line numbers
  - [ ] Search/replace
  - [ ] Word wrap toggle
  - [ ] Font size adjustment

---

## Phase 5: Advanced Features ⏳

**Goal**: Tabs, dual pane, search, and advanced functionality

### Tasks

#### 5.1 Tabs (0/1)
- [ ] Tab system
  - [ ] AdwTabView integration
  - [ ] New tab (Ctrl+T)
  - [ ] Close tab (Ctrl+W, middle-click)
  - [ ] Tab drag reorder
  - [ ] Tab with directory history
  - [ ] Duplicate tab
  - [ ] Reopen closed tab

#### 5.2 Dual Pane (0/1)
- [ ] DualPaneWidget
  - [ ] Side-by-side panes
  - [ ] Independent navigation
  - [ ] Copy/move between panes (F5/F6)
  - [ ] Synchronize navigation (optional)
  - [ ] Horizontal/vertical split
  - [ ] Resizeable separator

#### 5.3 Search (0/1)
- [ ] Search functionality
  - [ ] Search bar (Ctrl+F)
  - [ ] Filename search
  - [ ] Content search (via ripgrep/grep)
  - [ ] Search options:
    - [ ] Case sensitive
    - [ ] Regular expressions
    - [ ] Recursive search
    - [ ] Date filters
    - [ ] Size filters
    - [ ] Type filters
  - [ ] Results list with preview

#### 5.4 Archive Support (0/2)
- [ ] Archive viewer
  - [ ] Read ZIP files (adm-zip)
  - [ ] Read TAR/GZ files (tar)
  - [ ] Read 7z files (node-7z)
  - [ ] Read RAR files (node-unrar-js)
  - [ ] Display contents as virtual folder

- [ ] Archive extraction
  - [ ] Extract to location dialog
  - [ ] Extract to current directory
  - [ ] Progress for large archives
  - [ ] Password support

#### 5.5 Bookmarks (1/2)
- [x] Bookmarks in sidebar
- [ ] Add to bookmarks context action
  - [ ] Remove from bookmarks
  - [ ] Bookmark manager dialog
  - [ ] Drag to reorder

#### 5.6 Keyboard Shortcuts (1/1)
- [x] Shortcuts dialog (F1 or Ctrl+?)
  - [x] All shortcuts registered
  - [ ] Search in shortcuts
  - [ ] Customizable shortcuts (optional)

#### 5.7 Preferences Window (0/1)
- [ ] PreferencesWindow (Adw.PreferencesWindow)
  - [ ] View settings
    - [ ] Default view
    - [ ] Show hidden files
    - [ ] Sort options
    - [ ] Folders first
  - [ ] Thumbnail settings
    - [ ] Show thumbnails
    - [ ] Thumbnail size
    - [ ] Video preview on hover
  - [ ] Behavior settings
    - [ ] Confirm delete
    - [ ] Single-click to open
  - [ ] Appearance
    - [ ] Theme (follow system/dark/light)
    - [ ] Font size
    - [ ] Icon size

---

## Phase 6: Cloud Integration ⏳

**Goal**: Integrate with cloud storage providers

### Tasks

#### 6.1 Cloud Provider Architecture (0/1)
- [ ] CloudProvider interface
  - [ ] List files
  - [ ] Download file
  - [ ] Upload file
  - [ ] Create folder
  - [ ] Delete file
  - [ ] Get metadata

#### 6.2 Google Drive (0/1)
- [ ] GoogleDriveProvider
  - [ ] OAuth 2.0 flow
  - [ ] Token refresh handling
  - [ ] Browse files
  - [ ] Download files
  - [ ] Upload files
  - [ ] Sync status indicators

#### 6.3 Dropbox (0/1)
- [ ] DropboxProvider
  - [ ] OAuth 2.0 flow (PKCE)
  - [ ] Browse files
  - [ ] Download files
  - [ ] Upload files
  - [ ] Shared folder support

#### 6.4 Cloud UI Integration (0/1)
- [ ] Cloud storage in sidebar
  - [ ] Mount/unmount cloud drives
  - [ ] Connection status indicator
  - [ ] Account info display
  - [ ] Disconnect button

---

## Phase 7: Polish & Distribution ⏳

**Goal**: Performance optimization, testing, packaging

### Tasks

#### 7.1 Performance (0/1)
- [ ] Performance optimizations
  - [ ] Profile with sysprof
  - [ ] Optimize thumbnail generation
  - [ ] Lazy loading for large directories
  - [ ] Memory leak detection
  - [ ] Cache optimization

#### 7.2 Testing (0/1)
- [ ] Test suite
  - [ ] Unit tests for services
  - [ ] Integration tests
  - [ ] UI tests (dogtail/gtktest)
  - [ ] Test with 100K+ files
  - [ ] Test edge cases (permissions, symlinks, etc.)

#### 7.3 Accessibility (0/1)
- [ ] Accessibility improvements
  - [ ] Screen reader support
  - [ ] Keyboard navigation review
  - [ ] High contrast support
  - [ ] Reduced motion support

#### 7.4 Internationalization (0/1)
- [ ] i18n support
  - [ ] Extract strings for translation
  - [ ] Add common languages
  - [ ] RTL support
  - [ ] Translation documentation

#### 7.5 Packaging (0/1)
- [ ] Distribution packages
  - [ ] Flatpak manifest
  - [ ] Debian/Ubuntu package
  - [ ] Fedora/RPM package
  - [ ] Arch AUR PKGBUILD
  - [ ] Snap package (optional)
  - [ ] AppImage (optional)

#### 7.6 Documentation (0/1)
- [ ] Documentation
  - [ ] User manual
  - [ ] Developer guide
  - [ ] API documentation
  - [ ] Translators guide
  - [ ] Release notes

---

## Technology Stack

| Layer | Technology | Purpose |
|--------|-------------|-----------|
| UI Framework | GTK4 + LibAdwaita | Native GNOME/Ubuntu look |
| Language | Python 3.11+ | Rapid development |
| Build System | Meson + Ninja | Standard GNOME tools |
| State | GSettings | Desktop settings integration |
| File Ops | GIO/GLib | Async operations |
| PDF | Poppler | PDF rendering |
| Video | GStreamer + Gtk.MediaFile | Video playback |
| Images | GdkPixbuf | Image handling |
| Icons | Adwaita icon theme | Native icons |

## Memory Usage Target

| Component | Target | Notes |
|-----------|---------|-------|
| Base application | 30-50 MB | With no files loaded |
| With 1K files | 40-60 MB | List view |
| With thumbnails | 60-80 MB | Grid view with thumbs |
| With video preview | +10-20 MB | Temporary spike |

## Dependencies

### System
- GTK4 (>= 4.10)
- LibAdwaita (>= 1.2)
- GLib (>= 2.74)
- GIO (>= 2.74)

### Python
- PyGObject (>= 3.42)
- Python 3.11+

### Optional
- GStreamer (video playback, thumbnails)
- Poppler (PDF viewer)
- ffmpegthumbnailer (video thumbnails, faster than GStreamer)
- Pygments (text syntax highlighting)
- python-magic (better MIME detection)

## Release Roadmap

| Version | Planned Features | ETA |
|---------|------------------|------|
| 0.2.0 | File operations (copy, cut, paste, delete, rename) | Phase 2 |
| 0.3.0 | Thumbnails + video preview on hover | Phase 3 |
| 0.4.0 | Media viewers (image, PDF, video, text) | Phase 4 |
| 0.5.0 | Tabs, dual pane, search | Phase 5.1-5.3 |
| 0.6.0 | Archive support, bookmarks, preferences | Phase 5.4-5.7 |
| 0.7.0 | Cloud integration (Google Drive, Dropbox) | Phase 6 |
| 1.0.0 | Beta release - all features, polish | Phase 7 |

---

## How to Contribute

1. Fork the repository
2. Create a feature branch
3. Implement a task from this plan
4. Write tests
5. Submit a pull request

### Development Commands

```bash
# Run in development mode
python3 run.py

# Build with Meson
meson setup build
meson compile -C build

# Install (optional)
sudo meson install -C build

# Run tests
meson test -C build

# Profile
sysprof-cli -- python3 run.py
```

---

**Last Updated**: 2025-02-08
**Current Version**: 0.1.0-dev
