# 📸 GPS Photo Renamer

Automatically rename photos based on GPS EXIF data and datetime with intelligent counter functionality.

## Features

✨ **Smart Counter**: Automatically continues numbering from existing files  
🌍 **GPS Geocoding**: Converts GPS coordinates to city and country names  
💧 **Watermark Support**: Optional date and location watermarks  
🧹 **macOS Cleanup**: Removes `.DS_Store` and `._*` files automatically  
🔄 **Recursive Processing**: Process subdirectories  
🎯 **Skip Processed**: Avoids renaming already processed files  

## Output Format

Photos are renamed to: `YYYYMMDDHHMMSS_NNNN_City_CC.jpg`

**Example:**
```
Before: IMG_1234.JPG
After:  20241226093045_0001_Graz_AT.jpg
```

## Installation

### Prerequisites

- Python 3.7+
- macOS, Linux, or Windows

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/GPS-Photo-Renamer.git
cd GPS-Photo-Renamer
```

2. Create virtual environment:
```bash
python3 -m venv gps-renamer-env
source gps-renamer-env/bin/activate  # On Windows: gps-renamer-env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode (macOS)

Double-click `gps_photo_renamer.command` for an interactive experience.

### Command Line

Basic usage:
```bash
python3 gps_photo_renamer_smart_counter.py /path/to/photos
```

With watermark:
```bash
python3 gps_photo_renamer_smart_counter.py /path/to/photos --watermark
```

Dry-run (preview without renaming):
```bash
python3 gps_photo_renamer_smart_counter.py /path/to/photos --dry-run
```

Recursive processing:
```bash
python3 gps_photo_renamer_smart_counter.py /path/to/photos --recursive
```

### Command Line Options

```
positional arguments:
  directory            Directory containing photos

optional arguments:
  -h, --help           Show help message
  --api-key API_KEY    LocationIQ API key (optional)
  --no-geocoding       Disable geocoding (only use datetime)
  --dry-run            Preview changes without renaming
  --watermark          Add watermark with date and location
  --no-skip            Process already renamed files
  --recursive          Process subdirectories recursively
  --separator CHAR     Separator for filename parts (default: _)
```

## Geocoding Services

The tool uses multiple geocoding services in fallback order:

1. **Nominatim** (OpenStreetMap) - Free, no API key required
2. **LocationIQ** - Requires API key (optional)
3. **BigDataCloud** - Free, no API key required

Get a free LocationIQ API key at: https://locationiq.com/

## Watermark

When enabled, watermarks are added to images:
- **Top left**: Date (DD.MM.YYYY)
- **Top right**: Location (City - CC)

## Smart Counter

The smart counter automatically:
- Scans existing files matching the pattern `YYYYMMDDHHMMSS_NNNN`
- Finds the highest counter number
- Starts numbering new files from the next available number

**Example:**
```
Existing files: 20241226_0001.jpg, 20241226_0002.jpg
New files start at: 20241226_0003.jpg
```

## Supported Formats

- JPG/JPEG
- PNG
- HEIC/HEIF

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created with ❤️ for organizing photo collections

---

**Note:** This tool only processes images with valid EXIF data including datetime. Images without EXIF data or GPS coordinates will be skipped.
