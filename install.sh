#!/bin/bash
# UltraFiles Local Install Script

set -e

echo "Installing UltraFiles locally..."

# Define paths
INSTALL_DIR="$HOME/.local/share/ultrafiles"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Copy source files
echo "Copying source files to $INSTALL_DIR..."
cp -r src data run.py "$INSTALL_DIR/"

# Compile resources (just in case)
echo "Compiling resources..."
glib-compile-resources --sourcedir="$INSTALL_DIR/data/resources" \
    --target="$INSTALL_DIR/data/resources/ultrafiles.gresource" \
    "$INSTALL_DIR/data/resources/ultrafiles.gresource.xml"

# Install Icon
echo "Installing icon..."
cp data/icons/com.ultrafiles.UltraFiles.svg "$ICON_DIR/"

# Install Desktop File
echo "Installing desktop entry..."
sed "s|Exec=ultrafiles|Exec=$BIN_DIR/ultrafiles|" data/com.ultrafiles.UltraFiles.desktop.in > "$DESKTOP_DIR/com.ultrafiles.UltraFiles.desktop"
# Update icon path/name if needed, but it should be picked up by name
sed -i "s|Icon=system-file-manager|Icon=com.ultrafiles.UltraFiles|" "$DESKTOP_DIR/com.ultrafiles.UltraFiles.desktop"

# Create launcher script
echo "Creating launcher..."
cat > "$BIN_DIR/ultrafiles" <<EOF
#!/bin/bash
# Force OpenGL rendering
export GSK_RENDERER=gl
export GST_GL_WINDOW=gtk4
cd "$INSTALL_DIR"
python3 run.py "\$@"
EOF

chmod +x "$BIN_DIR/ultrafiles"

# Update caches
echo "Updating desktop database..."
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Done! You can now launch UltraFiles from your applications menu."
