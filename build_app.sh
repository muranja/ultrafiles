#!/bin/bash
set -e

echo "Building UltraFiles..."

# Ensure PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    python3 -m pip install pyinstaller || python3 -m pip install pyinstaller --break-system-packages
    export PATH="$PATH:$HOME/.local/bin"
fi

# Clean previous build
rm -rf build dist ultrafiles.spec

# Build
# --onefile: Create single executable
# --windowed: No console window
# --name: Output name
# --add-data: Include CSS and other assets if needed (e.g. src/css)
# --hidden-import: Ensure GI modules are found
# Note: PyGObject with PyInstaller can be tricky.
# We often need to collect data files for Girepository.
# For now, we try basic build. If it fails, we add hooks.

# Compile Resources
echo "Compiling resources..."
glib-compile-resources --target=ultrafiles.gresource --sourcedir=data/resources data/resources/ultrafiles.gresource.xml

# Compile Schemas
echo "Compiling schemas..."
glib-compile-schemas --targetdir=. data/

echo "Running PyInstaller..."
python3 -m pip install pyinstaller || python3 -m pip install pyinstaller --break-system-packages
export PATH="$PATH:$HOME/.local/bin"

pyinstaller --noconfirm --onefile --windowed --name "UltraFiles" \
    --hidden-import="gi" \
    --collect-all="gi" \
    --collect-data="glib" \
    --add-data="ultrafiles.gresource:." \
    --add-data="gschemas.compiled:." \
    run.py

# Cleanup
rm ultrafiles.gresource gschemas.compiled

echo "Build complete! Executable is in dist/UltraFiles"
ls -lh dist/UltraFiles
