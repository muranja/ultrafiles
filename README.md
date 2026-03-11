# UltraFiles

**State-of-the-Art Linux File Manager**

UltraFiles is a modern, high-performance file manager built with GTK4 and Python. It features a premium UI, advanced file operations, and power-user tools like integrated terminal, git status, and tagging.

## Features

- **Premium UI**: Sleek, adaptive design using LibAdwaita.
- **Advanced Navigation**: Split view, tabs, and sidebar with favorites.
- **Power Tools**:
  - **Git Integration**: View repo status and file changes directly in the grid.
  - **Integrated Terminal**: Built-in VTE terminal for command-line access.
  - **Rust-Powered Search**: Fast file search using `ripgrep`.
  - **Tags & Favorites**: Organize files with color-coded tags and quick access favorites.
- **Media Ready**:
  - **Thumbnails**: Async generation for images and videos.
  - **Hover Previews**: Play videos on hover.
  - **Built-in Viewer**: View images and videos without leaving the app.
- **Robust Operations**:
  - **Undo/Redo**: Safe file operations.
  - **Batch Rename**: Pattern-based renaming.
  - **Smart Metadata**: Edit audio/video tags.

## Installation

### Standalone (Recommended)

Download the latest release from the [Releases](https://github.com/vin/ultrafiles/releases) page.

```bash
chmod +x UltraFiles
./UltraFiles
```

### From Source

Requirements:

- Python 3.10+
- GTK4, LibAdwaita
- PyGObject, PyInstaller (for building)

```bash
# Clone
git clone https://github.com/vin/ultrafiles.git
cd ultrafiles

# Install dependencies (Ubuntu/Debian)
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-vte-2.91

# Run
python3 src/main.py
```

## Building

To build a standalone executable:

```bash
./build_app.sh
```

The output will be in `dist/UltraFiles`.

## License

MIT License. See [LICENSE](LICENSE) for details.
