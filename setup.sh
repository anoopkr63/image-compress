#!/bin/bash
# ImagePress — one-shot setup script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHELL_RC=""

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║    ImagePress — Setup               ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# 1. Create virtual environment
echo "  → Creating virtual environment..."
python3 -m venv "$SCRIPT_DIR/.venv"

# 2. Install dependencies
echo "  → Installing dependencies (Pillow + pymupdf)..."
"$SCRIPT_DIR/.venv/bin/pip" install --quiet Pillow pymupdf

# 3. Make imgpress executable
chmod +x "$SCRIPT_DIR/imgpress"

# 4. Detect shell config file
if [ -f "$HOME/.zshrc" ]; then
  SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
  SHELL_RC="$HOME/.bash_profile"
fi

# 5. Add to PATH (only once)
PATH_LINE="export PATH=\"$SCRIPT_DIR:\$PATH\"  # imagepress"
if [ -n "$SHELL_RC" ] && ! grep -q "# imagepress" "$SHELL_RC" 2>/dev/null; then
  echo "" >> "$SHELL_RC"
  echo "$PATH_LINE" >> "$SHELL_RC"
  echo "  → Added imgpress to PATH in $SHELL_RC"
else
  echo "  → PATH already configured, skipping."
fi

echo ""
echo "  ✔  Setup complete!"
echo ""
echo "  Open a new terminal tab, then run:"
echo "      imgpress --info          # see all options"
echo "      imgpress photo.jpg       # compress an image"
echo "      imgpress document.pdf    # convert PDF to images"
echo ""
