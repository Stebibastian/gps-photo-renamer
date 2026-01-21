#!/bin/bash
# GPS Photo Renamer
# Easy-to-use photo renaming tool with GPS location data

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║            📸  GPS PHOTO RENAMER  📸                      ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Automatically rename photos with date and location"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Virtual Environment exists
if [ ! -d "$HOME/gps-renamer-env" ]; then
    echo "⚠️  Virtual Environment not found!"
    echo ""
    echo "Creating Virtual Environment..."
    python3 -m venv ~/gps-renamer-env
    
    echo "Installing packages..."
    source ~/gps-renamer-env/bin/activate
    pip install Pillow requests --quiet
    echo "✅ Installation complete!"
    echo ""
else
    # Activate Virtual Environment
    source ~/gps-renamer-env/bin/activate
fi

# Show available USB drives / volumes
echo "📁 AVAILABLE USB DRIVES / VOLUMES:"
echo ""
ls -1 /Volumes/ | grep -v "Macintosh HD" | nl
echo ""

# Ask for USB drive selection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Enter number of USB drive (or ENTER for manual path): " choice
echo ""

if [ -z "$choice" ]; then
    # Manual path
    read -p "📂 Enter full path: " directory
else
    # Select from list
    directory="/Volumes/$(ls -1 /Volumes/ | grep -v "Macintosh HD" | sed -n "${choice}p")"
fi

# Check if directory exists
if [ ! -d "$directory" ]; then
    echo "❌ Error: Directory not found: $directory"
    echo ""
    read -p "Press ENTER to exit..."
    exit 1
fi

echo "✅ Selected: $directory"
echo ""

# Ask for watermark
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Add watermark? (Y/n): " watermark
watermark=${watermark:-Y}  # Default: Yes
echo ""

# Confirmation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 SUMMARY:"
echo ""
echo "   Directory:  $directory"
echo "   Watermark:  $watermark"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Continue? (Y/n): " confirm
confirm=${confirm:-Y}
echo ""

if [[ ! $confirm =~ ^[Yy] ]]; then
    echo "❌ Cancelled."
    echo ""
    read -p "Press ENTER to exit..."
    exit 0
fi

# Build command
script_path="$(dirname "$0")/gps_photo_renamer_smart_counter.py"

if [ ! -f "$script_path" ]; then
    echo "❌ Script not found: $script_path"
    echo ""
    read -p "Press ENTER to exit..."
    exit 1
fi

cmd="python3 \"$script_path\" \"$directory\""

if [[ $watermark =~ ^[Yy] ]]; then
    cmd="$cmd --watermark"
fi

# Start processing
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STARTING PROCESSING..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

eval $cmd

exit_code=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $exit_code -eq 0 ]; then
    echo "✅ DONE! All photos have been processed."
    echo ""
    echo "Your USB drive is ready! 📸"
else
    echo "❌ An error occurred."
    echo ""
    echo "See output above for details."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press ENTER to exit..."
