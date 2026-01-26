# 📸 GPS Photo Renamer

Automatically rename photos based on GPS EXIF data and datetime - with native macOS UI.

## Features

- 🖥️ **Native macOS App** - No Terminal required
- ✨ **Smart Counter** - Automatically continues numbering from existing files
- 🌍 **GPS Geocoding** - Converts GPS coordinates to city and country names
- 💧 **Watermark** - Date (top-left) and location (top-right)
- 🧹 **macOS Cleanup** - Removes `.DS_Store` and `._*` files automatically

## Output Format

```
Before: IMG_1234.JPG
After:  20241226093045_0001_Graz_AT.jpg
```

## Installation

1. Download or clone this repository
2. Move `GPS Photo Renamer.app` to your Applications folder
3. **Important:** Keep `gps_photo_renamer_smart_counter.py` in the same folder!
4. Double-click to start

**First Launch:** Right-click → "Open" → "Open" (bypasses Gatekeeper)

## Usage

1. **Select Folder** - Choose folder with photos
2. **Choose Mode** - Log preview or direct rename
3. **Confirm** - Review and start
4. **Done** - Open folder or rename after preview

## Requirements

- macOS 10.14+
- Python 3.7+
- Internet connection (for GPS location lookup)

Dependencies are installed automatically:
```bash
pip3 install Pillow requests --break-system-packages
```

## Supported Formats

- JPG / JPEG
- PNG
- HEIC / HEIF

## License

MIT License - See [LICENSE](LICENSE) file

---

Created with ❤️ for organizing photo collections
