#!/bin/bash

MULTISOBER_DIR="$HOME/MultiSober"
DESKTOP_ENTRY_DIR="$HOME/.local/share/applications"
ICON_URL="https://raw.githubusercontent.com/dim-ghub/MultiSober/refs/heads/main/MultiSober.svg"
PYTHON_SCRIPT_URL="https://raw.githubusercontent.com/dim-ghub/MultiSober/refs/heads/main/main.py"
ICON_PATH="$MULTISOBER_DIR/MultiSober.svg"
PYTHON_SCRIPT_PATH="$MULTISOBER_DIR/main.py"
DESKTOP_FILE_PATH="$DESKTOP_ENTRY_DIR/MultiSober.desktop"

echo "Starting MultiSober installation..."

echo "Creating directory: $MULTISOBER_DIR"
mkdir -p "$MULTISOBER_DIR" || { echo "Failed to create $MULTISOBER_DIR. Exiting."; exit 1; }

echo "Downloading icon from $ICON_URL to $ICON_PATH"
wget -O "$ICON_PATH" "$ICON_URL" || { echo "Failed to download icon. Exiting."; exit 1; }

echo "Downloading Python script from $PYTHON_SCRIPT_URL to $PYTHON_SCRIPT_PATH"
wget -O "$PYTHON_SCRIPT_PATH" "$PYTHON_SCRIPT_URL" || { echo "Failed to download Python script. Exiting."; exit 1; }

echo "Making Python script executable: $PYTHON_SCRIPT_PATH"
chmod +x "$PYTHON_SCRIPT_PATH" || { echo "Failed to make Python script executable. Exiting."; exit 1; }

echo "Creating desktop entry directory: $DESKTOP_ENTRY_DIR"
mkdir -p "$DESKTOP_ENTRY_DIR" || { echo "Failed to create $DESKTOP_ENTRY_DIR. Exiting."; exit 1; }

echo "Creating desktop file: $DESKTOP_FILE_PATH"
cat << EOF > "$DESKTOP_FILE_PATH"
[Desktop Entry]
Name=MultiSober
Comment=GUI application for MultiSober
Exec=python3 $PYTHON_SCRIPT_PATH
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;
EOF

echo "Making desktop file executable: $DESKTOP_FILE_PATH"
chmod +x "$DESKTOP_FILE_PATH" || { echo "Failed to make desktop file executable. Exiting."; exit 1; }

echo "MultiSober installation complete!"
echo "You might need to log out and log back in, or refresh your desktop environment for the application to appear in your menu."
echo "You can typically find it by searching for 'MultiSober' in your application launcher."
