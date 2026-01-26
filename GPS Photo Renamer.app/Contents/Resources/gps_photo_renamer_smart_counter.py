#!/usr/bin/env python3
"""
GPS Photo Renamer - Smart Counter Version
Renames photos based on GPS EXIF data and datetime.
Counter automatically continues from existing files.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import time

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    from PIL import ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests not installed. Install with: pip install requests")
    sys.exit(1)


class GPSPhotoRenamer:
    """Renames photos based on GPS coordinates and datetime from EXIF data."""

    PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.3gp', '.webm', '.insv', '.lrv'}
    
    def __init__(self, api_key: Optional[str] = None, use_geocoding: bool = True):
        """
        Initialize the renamer.
        
        Args:
            api_key: LocationIQ API key (optional, will try Nominatim first)
            use_geocoding: Whether to use geocoding services
        """
        self.api_key = api_key
        self.use_geocoding = use_geocoding
        self.geocode_cache = {}
        
    def get_exif_data(self, image_path: Path) -> Optional[dict]:
        """Extract EXIF data from image."""
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            if not exif_data:
                return None
                
            exif = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                exif[tag] = value
                
            return exif
        except Exception as e:
            print(f"  ⚠️  Error reading EXIF: {e}")
            return None
    
    def get_gps_data(self, exif: dict) -> Optional[Dict[str, float]]:
        """Extract GPS coordinates from EXIF data."""
        if 'GPSInfo' not in exif:
            return None
            
        gps_info = {}
        for key in exif['GPSInfo'].keys():
            decode = GPSTAGS.get(key, key)
            gps_info[decode] = exif['GPSInfo'][key]
        
        def convert_to_degrees(value):
            """Convert GPS coordinates to degrees."""
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)
        
        try:
            lat = convert_to_degrees(gps_info['GPSLatitude'])
            if gps_info['GPSLatitudeRef'] == 'S':
                lat = -lat
                
            lon = convert_to_degrees(gps_info['GPSLongitude'])
            if gps_info['GPSLongitudeRef'] == 'W':
                lon = -lon
                
            return {'latitude': lat, 'longitude': lon}
        except KeyError:
            return None
    
    def forward_geocode(self, city: str, country_code: str) -> Optional[Dict[str, float]]:
        """
        Forward geocode: Convert city name + country to coordinates.
        Used for reprocessing photos that lost their EXIF GPS data.
        """
        cache_key = f"fwd:{city}:{country_code}"
        if cache_key in self.geocode_cache:
            return self.geocode_cache[cache_key]

        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': f"{city}, {country_code}",
                'format': 'json',
                'limit': 1
            }
            headers = {'User-Agent': 'GPSPhotoRenamer/2.4'}

            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = {
                        'latitude': float(data[0]['lat']),
                        'longitude': float(data[0]['lon'])
                    }
                    self.geocode_cache[cache_key] = result
                    print(f"    📍 Forward geocoded {city}, {country_code} → {result['latitude']:.4f}, {result['longitude']:.4f}")
                    return result
        except Exception as e:
            print(f"  ⚠️  Forward geocoding failed: {e}")

        return None

    def geocode_location(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """
        Reverse geocode coordinates to location name.
        Tries Nominatim first, then LocationIQ, then BigDataCloud.
        """
        if not self.use_geocoding:
            return None
            
        cache_key = f"{lat:.4f},{lon:.4f}"
        if cache_key in self.geocode_cache:
            return self.geocode_cache[cache_key]
        
        # Try Nominatim first (free, no API key needed)
        result = self._try_nominatim(lat, lon)
        if result:
            self.geocode_cache[cache_key] = result
            return result
        
        time.sleep(1)  # Rate limiting
        
        # Try LocationIQ if API key provided
        if self.api_key:
            result = self._try_locationiq(lat, lon)
            if result:
                self.geocode_cache[cache_key] = result
                return result
            time.sleep(1)
        
        # Try BigDataCloud as fallback (free, no API key)
        result = self._try_bigdatacloud(lat, lon)
        if result:
            self.geocode_cache[cache_key] = result
            return result
        
        # If all services fail, return coordinates
        coord_str = f"{lat:.5f}"
        return {
            'city': coord_str,
            'city_display': coord_str,
            'country_code': f"{lon:.5f}"
        }
    
    def _try_nominatim(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """Try OpenStreetMap Nominatim for reverse geocoding."""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'zoom': 10
            }
            headers = {'User-Agent': 'GPSPhotoRenamer/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                city = (address.get('city') or
                       address.get('town') or
                       address.get('village') or
                       address.get('municipality') or
                       address.get('county', 'Unknown'))

                country_code = address.get('country_code', 'XX').upper()

                return {
                    'city': self._clean_location_name_for_filename(city),
                    'city_display': self._clean_location_name_for_display(city),
                    'country_code': country_code
                }
        except Exception as e:
            print(f"  ⚠️  Nominatim error: {e}")
        return None

    def _try_locationiq(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """Try LocationIQ for reverse geocoding."""
        try:
            url = "https://us1.locationiq.com/v1/reverse.php"
            params = {
                'key': self.api_key,
                'lat': lat,
                'lon': lon,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                city = (address.get('city') or
                       address.get('town') or
                       address.get('village') or
                       address.get('county', 'Unknown'))

                country_code = address.get('country_code', 'XX').upper()

                return {
                    'city': self._clean_location_name_for_filename(city),
                    'city_display': self._clean_location_name_for_display(city),
                    'country_code': country_code
                }
        except Exception as e:
            print(f"  ⚠️  LocationIQ error: {e}")
        return None

    def _try_bigdatacloud(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """Try BigDataCloud for reverse geocoding (free, no API key)."""
        try:
            url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
            params = {
                'latitude': lat,
                'longitude': lon,
                'localityLanguage': 'en'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                city = (data.get('city') or
                       data.get('locality') or
                       data.get('principalSubdivision', 'Unknown'))

                country_code = data.get('countryCode', 'XX')

                return {
                    'city': self._clean_location_name_for_filename(city),
                    'city_display': self._clean_location_name_for_display(city),
                    'country_code': country_code
                }
        except Exception as e:
            print(f"  ⚠️  BigDataCloud error: {e}")
        return None
    
    def _clean_location_name_for_filename(self, name: str) -> str:
        """Clean location name for use in filename (no spaces)."""
        # Remove special characters but keep umlauts
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with nothing for filenames
        name = name.replace(' ', '')
        return name

    def _clean_location_name_for_display(self, name: str) -> str:
        """Clean location name for display (keep spaces)."""
        # Remove only truly problematic characters, keep spaces
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        return name

    def get_map_tile(self, lat: float, lon: float, size: int = 200, zoom: int = 13) -> Optional[Image.Image]:
        """
        Download a map tile from OpenStreetMap centered on given coordinates.

        Args:
            lat: Latitude
            lon: Longitude
            size: Size of the map square in pixels (default 200x200)
            zoom: Zoom level (default 13 - shows neighborhood/village)

        Returns:
            PIL Image of the map tile or None if failed
        """
        try:
            import math
            from io import BytesIO

            # Convert lat/lon to PRECISE pixel position in world coordinates
            n = 2 ** zoom

            # Precise floating-point tile coordinates
            x_tile_float = (lon + 180) / 360 * n
            y_tile_float = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n

            # Integer tile numbers
            x_tile = int(x_tile_float)
            y_tile = int(y_tile_float)

            # Precise pixel position within the tile grid (sub-pixel accuracy)
            x_pixel_precise = (x_tile_float - x_tile) * 256
            y_pixel_precise = (y_tile_float - y_tile) * 256

            # We need to fetch multiple tiles to get a centered view
            # Use 3x3 for better centering precision
            tiles_needed = 3

            # Create a larger canvas to stitch tiles
            canvas_size = 256 * tiles_needed
            canvas = Image.new('RGB', (canvas_size, canvas_size))

            # Fetch tiles in a grid around the center tile
            headers = {
                'User-Agent': 'GPSPhotoRenamer/2.5 (photo organization tool)'
            }

            # Calculate starting tile offset (center the target tile)
            start_offset = tiles_needed // 2

            for dx in range(tiles_needed):
                for dy in range(tiles_needed):
                    tile_x = x_tile + dx - start_offset
                    tile_y = y_tile + dy - start_offset

                    # OpenStreetMap tile URL
                    url = f"https://tile.openstreetmap.org/{zoom}/{tile_x}/{tile_y}.png"

                    try:
                        response = requests.get(url, headers=headers, timeout=5)
                        if response.status_code == 200:
                            tile_img = Image.open(BytesIO(response.content))
                            canvas.paste(tile_img, (dx * 256, dy * 256))
                    except Exception:
                        # If tile fetch fails, leave it blank
                        pass

            # Calculate the PRECISE position of coordinates on the canvas
            # The target tile is at position (start_offset * 256, start_offset * 256)
            # Add the sub-tile pixel offset
            exact_x = start_offset * 256 + x_pixel_precise
            exact_y = start_offset * 256 + y_pixel_precise

            # Calculate crop box centered on the EXACT coordinate position
            left = int(exact_x - size / 2)
            top = int(exact_y - size / 2)

            # Ensure we don't go outside canvas bounds
            if left < 0:
                left = 0
            if top < 0:
                top = 0
            if left + size > canvas_size:
                left = canvas_size - size
            if top + size > canvas_size:
                top = canvas_size - size

            right = left + size
            bottom = top + size

            # Crop to desired size
            map_img = canvas.crop((left, top, right, bottom))

            # WICHTIG: Sicherstellen dass die Karte EXAKT die gewünschte Grösse hat
            actual_width, actual_height = map_img.size
            if actual_width != size or actual_height != size:
                map_img = map_img.resize((size, size), Image.Resampling.LANCZOS)

            # Pin ist IMMER in der Mitte, da die Karte auf die Koordinaten zentriert wird
            from PIL import ImageDraw as MapDraw
            draw = MapDraw.Draw(map_img)

            # Pin-Position = Kartenmitte
            pin_x = size // 2
            pin_y = size // 2

            # Grösserer, klassischer Map-Pin
            pin_radius = 10  # Kreis-Radius

            # Schatten
            shadow_offset = 3
            draw.ellipse(
                [pin_x - pin_radius + shadow_offset, pin_y - pin_radius * 2 + shadow_offset,
                 pin_x + pin_radius + shadow_offset, pin_y + shadow_offset],
                fill=(0, 0, 0, 100)
            )

            # Roter Pin-Körper (Tropfenform nach oben)
            draw.ellipse(
                [pin_x - pin_radius, pin_y - pin_radius * 2,
                 pin_x + pin_radius, pin_y],
                fill=(220, 50, 50),
                outline=(255, 255, 255),
                width=2
            )

            # Weisser Punkt in der Mitte des Kreises
            dot_radius = 4
            dot_center_y = pin_y - pin_radius
            draw.ellipse(
                [pin_x - dot_radius, dot_center_y - dot_radius,
                 pin_x + dot_radius, dot_center_y + dot_radius],
                fill=(255, 255, 255)
            )

            # Spitze nach unten (zeigt auf die exakte Position)
            draw.polygon(
                [(pin_x, pin_y + 6),      # Spitze unten
                 (pin_x - 6, pin_y - 2),  # Links
                 (pin_x + 6, pin_y - 2)], # Rechts
                fill=(220, 50, 50),
                outline=(255, 255, 255)
            )

            return map_img

        except Exception as e:
            print(f"  ⚠️  Could not fetch map tile: {e}")
            return None
    
    def get_datetime_from_exif(self, exif: dict, file_path: Path = None) -> Optional[str]:
        """Extract datetime from EXIF and format it. Falls back to file modification date."""
        datetime_tags = ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']

        for tag in datetime_tags:
            if tag in exif:
                try:
                    dt_str = exif[tag]
                    dt = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                    return dt.strftime('%Y%m%d%H%M%S')
                except (ValueError, TypeError):
                    continue

        # Fallback: Use file modification date (for Insta360 and other cameras without EXIF date)
        if file_path and file_path.exists():
            try:
                mtime = file_path.stat().st_mtime
                dt = datetime.fromtimestamp(mtime)
                print(f"  ℹ️  Using file date (no EXIF date): {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                return dt.strftime('%Y%m%d%H%M%S')
            except Exception:
                pass

        return None
    
    def add_watermark_to_image(self, image_path: Path, datetime_str: Optional[str],
                               location: Optional[Dict] = None,
                               gps_coords: Optional[Dict[str, float]] = None,
                               add_map: bool = True, map_only: bool = False,
                               map_size: int = 280, map_opacity: int = 70, map_zoom: int = 13) -> bool:
        """
        Add watermark to image with date/time on left, location on right,
        and optional map tile below the location text.
        Respects EXIF orientation to handle portrait/landscape correctly.

        Args:
            image_path: Path to image file
            datetime_str: Datetime string in format YYYYMMDDHHMMSS
            location: Dictionary with 'city' and 'country_code' keys
            gps_coords: Dictionary with 'latitude' and 'longitude' keys for map
            add_map: If True, add map tile (default True)
            map_only: If True, only add map (for reprocessing existing photos)
            map_size: Size of map in percent of image (default: 15 = 15%)
            map_opacity: Opacity of map in percent (default: 70)
            map_zoom: Zoom level for map (default: 13)

        Returns:
            True if watermark was added successfully
        """
        try:
            # Open image
            img = Image.open(image_path)

            # WICHTIG: EXIF-Daten speichern bevor wir das Bild bearbeiten
            original_exif = None
            modified_exif = None
            try:
                original_exif = img.info.get('exif')

                # Versuche piexif zu verwenden um Orientierung zu korrigieren
                if original_exif:
                    try:
                        import piexif
                        exif_dict = piexif.load(original_exif)
                        # Setze Orientierung auf 1 (Normal) da wir das Bild drehen
                        if piexif.ImageIFD.Orientation in exif_dict.get("0th", {}):
                            exif_dict["0th"][piexif.ImageIFD.Orientation] = 1
                        modified_exif = piexif.dump(exif_dict)
                    except ImportError:
                        # piexif nicht installiert - EXIF nicht speichern um Doppeldrehung zu vermeiden
                        print(f"  ℹ️  piexif not installed - EXIF orientation may cause issues")
                        modified_exif = None
                    except Exception as e:
                        # Bei Fehler EXIF nicht speichern
                        modified_exif = None
            except Exception:
                pass

            # WICHTIG: EXIF-Orientierung auslesen und Bild korrekt drehen
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception as e:
                print(f"  ⚠️  Could not apply EXIF orientation: {e}")

            # Convert to RGBA for watermark
            img = img.convert('RGBA')

            # Create drawing overlay
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Calculate font size (4% of smallest dimension)
            min_dimension = min(img.size)
            font_size = int(min_dimension * 0.04)

            # Try to load font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()

            padding = int(font_size * 0.5)
            right_text_width = 0
            right_text_height = 0
            right_x = img.size[0] - padding  # Default right edge

            # Skip text watermarks if map_only mode
            if not map_only:
                # LEFT WATERMARK: Date only (no time)
                if datetime_str:
                    # Parse datetime string (YYYYMMDDHHMMSS) - nur Datum!
                    if len(datetime_str) >= 8:
                        date_part = f"{datetime_str[6:8]}.{datetime_str[4:6]}.{datetime_str[0:4]}"
                    else:
                        date_part = datetime_str[:8]

                    # Single line text - nur Datum
                    left_text = date_part

                    # Get text bounding box (single line)
                    bbox = draw.textbbox((0, 0), left_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                    # Position
                    x = padding
                    y = padding

                    # Background rectangle
                    draw.rectangle(
                        [x - padding//2, y - padding//2,
                         x + text_width + padding//2, y + text_height + padding//2],
                        fill=(0, 0, 0, 180)
                    )

                    # Text (single line)
                    draw.text((x, y), left_text, font=font, fill=(255, 255, 255, 255))

                # RIGHT WATERMARK: City - Country (only if GPS exists)
                if location and location.get('city'):
                    # Verwende city_display für Anzeige (mit Leerzeichen), fallback auf city
                    display_city = location.get('city_display', location['city'])
                    right_text = f"{display_city} - {location['country_code']}"

                    # Get text bounding box
                    bbox = draw.textbbox((0, 0), right_text, font=font)
                    right_text_width = bbox[2] - bbox[0]
                    right_text_height = bbox[3] - bbox[1]

                    # Position (top right)
                    right_x = img.size[0] - right_text_width - padding * 2
                    y = padding

                    # Background rectangle
                    draw.rectangle(
                        [right_x - padding//2, y - padding//2,
                         right_x + right_text_width + padding//2, y + right_text_height + padding//2],
                        fill=(0, 0, 0, 180)
                    )

                    # Text
                    draw.text((right_x, y), right_text, font=font, fill=(255, 255, 255, 255))

            # Composite text overlay first
            img = Image.alpha_composite(img, overlay)

            # MAP TILE: Below the location text, aligned to right edge
            if add_map and gps_coords and gps_coords.get('latitude') and gps_coords.get('longitude'):
                try:
                    # Kartengrösse PROZENTUAL (map_size als Prozent der kleinsten Dimension)
                    # KEIN Maximum - immer proportional zum Bild
                    actual_map_size = int(min_dimension * map_size / 100)

                    # Nur Minimum für Lesbarkeit
                    actual_map_size = max(100, actual_map_size)

                    # DEBUG: Zeige berechnete Werte
                    print(f"    [MAP] min_dimension={min_dimension}, map_size={map_size}%, actual={actual_map_size}px, zoom={map_zoom}")

                    # Fetch map tile with user-configurable zoom
                    map_img = self.get_map_tile(
                        gps_coords['latitude'],
                        gps_coords['longitude'],
                        size=actual_map_size,
                        zoom=map_zoom
                    )

                    if map_img:
                        # Convert map to RGBA
                        map_img = map_img.convert('RGBA')

                        # Apply user-configurable opacity
                        opacity_factor = map_opacity / 100.0
                        alpha = map_img.split()[3] if map_img.mode == 'RGBA' else Image.new('L', map_img.size, 255)
                        alpha = alpha.point(lambda p: int(p * opacity_factor))

                        # Make map semi-transparent
                        map_rgba = Image.new('RGBA', map_img.size, (0, 0, 0, 0))
                        map_rgba.paste(map_img, (0, 0))
                        map_rgba.putalpha(alpha)

                        # Dünner schwarzer Rand
                        map_padding = max(3, padding // 6)

                        # Create background overlay on main image
                        bg_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                        bg_draw = ImageDraw.Draw(bg_overlay)

                        # Position: BÜNDIG mit dem Text-Hintergrund (gleicher rechter Rand)
                        text_right_edge = img.size[0] - padding - padding // 2
                        map_x = text_right_edge - actual_map_size - map_padding

                        # Vertical position: DIREKT unter dem Text (minimaler Abstand)
                        # Text-Box endet bei: y + text_height + padding//2 = padding + text_height + padding//2
                        if right_text_height > 0:
                            text_box_bottom = padding + right_text_height + padding // 2
                        else:
                            text_box_bottom = padding + font_size + padding // 2
                        # Minimaler Abstand: nur map_padding
                        map_y = text_box_bottom + map_padding

                        # Draw black background rectangle
                        bg_draw.rectangle(
                            [map_x - map_padding, map_y - map_padding,
                             map_x + actual_map_size + map_padding, map_y + actual_map_size + map_padding],
                            fill=(0, 0, 0, 180)
                        )

                        # Composite background
                        img = Image.alpha_composite(img, bg_overlay)

                        # Paste the semi-transparent map
                        img.paste(map_rgba, (map_x, map_y), map_rgba)

                        print(f"  🗺️  Map added ({actual_map_size}x{actual_map_size}px, {map_opacity}% opacity, zoom {map_zoom})")

                except Exception as e:
                    print(f"  ⚠️  Could not add map: {e}")

            # Convert back to RGB and save
            img = img.convert('RGB')

            # Save with corrected EXIF data (orientation = 1) if available
            # WICHTIG: Wir verwenden modified_exif wo Orientierung auf 1 gesetzt ist,
            # da das Bild bereits mit exif_transpose() gedreht wurde.
            # Wenn wir original_exif verwenden würden, würde der Viewer das Bild nochmal drehen!
            if modified_exif:
                img.save(image_path, quality=95, exif=modified_exif)
                print(f"  ✓ Saved with EXIF (orientation corrected)")
            else:
                # Ohne EXIF speichern - sicherer als mit falscher Orientierung
                img.save(image_path, quality=95)
                print(f"  ✓ Saved without EXIF (to avoid orientation issues)")

            return True

        except Exception as e:
            print(f"  ⚠️  Watermark error: {e}")
            return False
    
    def is_already_processed(self, filename: str) -> bool:
        """
        Check if filename matches the pattern of already processed files.
        Pattern: YYYYMMDDHHMMSS_NNNN[_Location_CC][_MAP].ext
        """
        # Pattern: starts with 12-14 digits, underscore, 4 digits
        pattern = r'^\d{12,14}_\d{4}'
        return bool(re.match(pattern, filename))

    def has_map_tag(self, filename: str) -> bool:
        """Check if filename already has _MAP tag."""
        # Remove extension and check for _MAP at the end
        name_without_ext = Path(filename).stem
        return name_without_ext.endswith('_MAP')
    
    def _get_start_counter(self, directory: Path) -> int:
        """
        Smart counter: Finds highest number in already processed files.
        """
        max_counter = 0
        pattern = re.compile(r'^\d{12,14}_(\d{4})')
        
        # Scanne alle Dateien im Verzeichnis
        for file in directory.iterdir():
            if file.is_file():
                match = pattern.match(file.name)
                if match:
                    counter = int(match.group(1))
                    max_counter = max(max_counter, counter)
        
        # Starte bei nächster Nummer
        return max_counter + 1
    
    def _collect_photo_files(self, directory: Path, recursive: bool) -> List[Path]:
        """
        Collect all photo files from directory.
        FILTERS OUT macOS system files (._* and .DS_Store)
        """
        photo_files = []
        
        if recursive:
            for ext in self.PHOTO_EXTENSIONS:
                for file in directory.rglob(f'*{ext}'):
                    # FILTER macOS files
                    if file.name.startswith('._'):
                        continue
                    if file.name == '.DS_Store':
                        continue
                    photo_files.append(file)
                for file in directory.rglob(f'*{ext.upper()}'):
                    # FILTER macOS files
                    if file.name.startswith('._'):
                        continue
                    if file.name == '.DS_Store':
                        continue
                    photo_files.append(file)
        else:
            for ext in self.PHOTO_EXTENSIONS:
                for file in directory.glob(f'*{ext}'):
                    # FILTER macOS files
                    if file.name.startswith('._'):
                        continue
                    if file.name == '.DS_Store':
                        continue
                    photo_files.append(file)
                for file in directory.glob(f'*{ext.upper()}'):
                    # FILTER macOS files
                    if file.name.startswith('._'):
                        continue
                    if file.name == '.DS_Store':
                        continue
                    photo_files.append(file)
        
        return sorted(set(photo_files))
    
    def find_video_files(self, directory: Path, recursive: bool = False) -> List[Path]:
        """
        Find all video files in directory.
        Returns list of video file paths.
        """
        video_files = []

        if recursive:
            for ext in self.VIDEO_EXTENSIONS:
                for file in directory.rglob(f'*{ext}'):
                    if file.name.startswith('._'):
                        continue
                    video_files.append(file)
                for file in directory.rglob(f'*{ext.upper()}'):
                    if file.name.startswith('._'):
                        continue
                    video_files.append(file)
        else:
            for ext in self.VIDEO_EXTENSIONS:
                for file in directory.glob(f'*{ext}'):
                    if file.name.startswith('._'):
                        continue
                    video_files.append(file)
                for file in directory.glob(f'*{ext.upper()}'):
                    if file.name.startswith('._'):
                        continue
                    video_files.append(file)

        return sorted(set(video_files))

    def cleanup_macos_files(self, directory: Path) -> None:
        """
        Delete macOS system files (.DS_Store and ._* resource forks).
        """
        deleted_count = 0

        # Delete .DS_Store files
        for ds_store in directory.rglob('.DS_Store'):
            try:
                ds_store.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"  ⚠️  Error deleting {ds_store.name}: {e}")

        # Delete ._* resource fork files
        for resource_fork in directory.rglob('._*'):
            try:
                resource_fork.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"  ⚠️  Error deleting {resource_fork.name}: {e}")

        if deleted_count > 0:
            print(f"\n🗑️  {deleted_count} macOS system files deleted")
        else:
            print(f"\n✓ No macOS system files found")
    
    def process_directory(self, directory: Path, dry_run: bool = False,
                         add_watermark: bool = False, add_map: bool = False,
                         map_size: int = 280, map_opacity: int = 70, map_zoom: int = 13,
                         reprocess_map: bool = False, skip_processed: bool = True,
                         recursive: bool = False, separator: str = '_'):
        """
        Process all photos in directory.

        Args:
            directory: Directory containing photos
            dry_run: If True, only show what would be renamed
            add_watermark: If True, add watermark to images
            add_map: If True, add map tile to images
            map_size: Size of map in percent of image (default: 15 = 15%)
            map_opacity: Opacity of map in percent (default: 70)
            map_zoom: Zoom level for map (default: 13)
            reprocess_map: If True, add map to already processed files without _MAP tag
            skip_processed: If True, skip files that match the processed pattern
            recursive: If True, process subdirectories recursively
            separator: Separator to use in filename (default: _)
        """
        print("\n" + "="*60)
        print("📸 GPS PHOTO RENAMER - SMART COUNTER EDITION")
        print("="*60)
        print(f"Directory:    {directory}")
        print(f"Geocoding:    {'Yes' if self.use_geocoding else 'No'}")
        if add_watermark:
            print(f"Watermark:    Yes (Date left, Location right)")
        if add_map:
            print(f"Map:          Yes ({map_size}px, {map_opacity}% opacity, zoom {map_zoom})")
        if reprocess_map:
            print(f"Reprocess:    Yes (Add map to existing photos)")
        print("="*60)

        # Smart counter: Find highest number
        counter = self._get_start_counter(directory)
        if counter > 1:
            print(f"\n🔢 Smart Counter: Starting at {counter:04d} (highest found: {counter-1:04d})")

        # Collect photo files (filters macOS files)
        photo_files = self._collect_photo_files(directory, recursive)

        print(f"\n📸 Found photos: {len(photo_files)}")
        print("="*60)

        if not photo_files:
            print("No photos found!")
            return

        if dry_run:
            print("\n🔍 DRY-RUN mode - Files will NOT be renamed\n")
        
        renamed_count = 0
        skipped_count = 0
        map_added_count = 0

        for idx, photo_path in enumerate(photo_files, 1):
            print(f"\n[{idx}/{len(photo_files)}] Processing: {photo_path.name}")

            # Check if already processed
            is_processed = self.is_already_processed(photo_path.name)
            has_map = self.has_map_tag(photo_path.name)

            # Debug output for reprocess mode
            if reprocess_map:
                print(f"    [DEBUG] is_processed={is_processed}, has_map={has_map}, add_map={add_map}")

            # Handle reprocess_map mode: Add map to already processed files without _MAP
            if is_processed and reprocess_map and add_map and not has_map:
                print(f"  🗺️  Adding map to existing file...")

                # Extract datetime from filename (first 14 digits)
                match = re.match(r'^(\d{12,14})', photo_path.name)
                datetime_str = match.group(1) if match else None

                # Extract location from filename - more flexible pattern
                # Handles: 20241226093045_0001_Graz_AT.jpg
                #          20241226093045_0001_NewYork_US.jpg
                #          20241226093045_0001_San-Francisco_US.jpg
                #          20241226093045_0001_Dübendorf_CH_MAP.jpg
                location = None
                # Pattern: after the counter (4 digits), get everything until the country code (2 uppercase letters)
                # The country code must be followed by either _MAP, .jpg, .jpeg, .png, .heic, etc.
                loc_match = re.search(r'_\d{4}_(.+)_([A-Z]{2})(?:_MAP)?\.', photo_path.name, re.IGNORECASE)
                if loc_match:
                    location = {'city': loc_match.group(1), 'country_code': loc_match.group(2)}
                    print(f"    📍 Extracted location: {location['city']}, {location['country_code']}")

                # Try to get GPS from EXIF first
                exif = self.get_exif_data(photo_path)
                gps_data = self.get_gps_data(exif) if exif else None

                # If no GPS in EXIF but we have location from filename, use forward geocoding
                if not gps_data and location:
                    print(f"    ℹ️  No GPS in EXIF, trying forward geocoding from filename...")
                    gps_data = self.forward_geocode(location['city'], location['country_code'])
                    if gps_data:
                        time.sleep(1)  # Rate limiting for Nominatim

                if not gps_data:
                    if not location:
                        print(f"  ⚠️  No GPS in EXIF and no location in filename - cannot add map")
                    else:
                        print(f"  ⚠️  Forward geocoding failed for {location['city']}, {location['country_code']}")
                    skipped_count += 1
                    continue

                if dry_run:
                    print(f"  [DRY-RUN] Would add map to: {photo_path.name}")
                    map_added_count += 1
                    continue

                # Add map watermark with user settings
                success = self.add_watermark_to_image(
                    photo_path, datetime_str, location, gps_data,
                    map_only=True, map_size=map_size, map_opacity=map_opacity, map_zoom=map_zoom
                )

                if success:
                    # Rename file to add _MAP tag
                    stem = photo_path.stem
                    new_name = f"{stem}_MAP{photo_path.suffix}"
                    new_path = photo_path.parent / new_name
                    photo_path.rename(new_path)
                    print(f"    ✓ {new_name}")
                    map_added_count += 1
                else:
                    print(f"  ❌ Failed to add map")
                    skipped_count += 1
                continue

            # Normal skip for already processed files
            if skip_processed and is_processed:
                print(f"  ⏭️  Skipped (already processed)")
                skipped_count += 1
                continue

            # Extract EXIF data (may be None for some cameras)
            exif = self.get_exif_data(photo_path)
            if not exif:
                exif = {}  # Use empty dict, will fall back to file date

            # Get datetime (with file date fallback for Insta360 etc.)
            datetime_str = self.get_datetime_from_exif(exif, photo_path)
            if not datetime_str:
                print(f"  ⚠️  No date found (EXIF or file)")
                continue

            # Get GPS data
            gps_data = self.get_gps_data(exif) if exif else None
            location = None

            if gps_data:
                lat = gps_data['latitude']
                lon = gps_data['longitude']
                location = self.geocode_location(lat, lon)
            else:
                print(f"  ⚠️  No GPS data")

            # Build new filename
            base_name = f"{datetime_str}{separator}{counter:04d}"

            if location:
                city = location['city']
                country = location['country_code']
                # Add _MAP tag if map is enabled and GPS exists
                map_tag = "_MAP" if add_map and gps_data else ""
                new_name = f"{base_name}{separator}{city}{separator}{country}{map_tag}{photo_path.suffix}"
            else:
                new_name = f"{base_name}{photo_path.suffix}"

            new_path = photo_path.parent / new_name

            # Rename file
            if not dry_run:
                try:
                    photo_path.rename(new_path)
                    print(f"  ✓ {photo_path.name}")
                    print(f"    → {new_name}")

                    # Add watermark if requested (with map if GPS available and map enabled)
                    if add_watermark:
                        self.add_watermark_to_image(
                            new_path, datetime_str, location, gps_data,
                            add_map=add_map, map_size=map_size, map_opacity=map_opacity, map_zoom=map_zoom
                        )

                    if location:
                        print(f"    📍 {location['city']}, {location['country_code']}")

                    renamed_count += 1
                    counter += 1
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            else:
                print(f"  ✓ {photo_path.name}")
                print(f"    → {new_name}")
                if location:
                    print(f"    📍 {location['city']}, {location['country_code']}")
                renamed_count += 1
                counter += 1
        
        # Clean up macOS files if not dry-run
        if not dry_run:
            self.cleanup_macos_files(directory)

        # Find video files
        video_files = self.find_video_files(directory, recursive)
        video_count = len(video_files)

        # Summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"Found:        {len(photo_files)}")
        print(f"Processed:    {renamed_count}")
        print(f"Skipped:      {skipped_count}")
        if map_added_count > 0:
            print(f"Maps added:   {map_added_count}")
        if video_count > 0:
            print(f"Videos:       {video_count}")
            # Calculate total size of videos
            total_size = sum(f.stat().st_size for f in video_files)
            size_mb = total_size / (1024 * 1024)
            print(f"Video Size:   {size_mb:.1f} MB")
            # List video files
            print("\n🎬 Video files found:")
            for vf in video_files:
                vf_size = vf.stat().st_size / (1024 * 1024)
                print(f"  • {vf.name} ({vf_size:.1f} MB)")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Rename photos based on GPS EXIF data and datetime'
    )
    parser.add_argument('directory', type=str, help='Directory containing photos')
    parser.add_argument('--api-key', type=str, help='LocationIQ API key (optional)')
    parser.add_argument('--no-geocoding', action='store_true',
                       help='Disable geocoding (only use datetime)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be renamed without actually renaming')
    parser.add_argument('--watermark', action='store_true',
                       help='Add watermark with date/time and location')
    parser.add_argument('--map', action='store_true',
                       help='Add map tile watermark with GPS location')
    parser.add_argument('--map-size', type=int, default=15,
                       help='Map size in percent of image (default: 15 = 15%%)')
    parser.add_argument('--map-opacity', type=int, default=70,
                       help='Map opacity in percent (default: 70)')
    parser.add_argument('--map-zoom', type=int, default=13,
                       help='Map zoom level (default: 13)')
    parser.add_argument('--reprocess-map', action='store_true',
                       help='Reprocess already renamed files to add map')
    parser.add_argument('--no-skip', action='store_true',
                       help='Process already renamed files')
    parser.add_argument('--recursive', action='store_true',
                       help='Process subdirectories recursively')
    parser.add_argument('--separator', type=str, default='_',
                       help='Separator character for filename parts (default: _)')

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    renamer = GPSPhotoRenamer(
        api_key=args.api_key,
        use_geocoding=not args.no_geocoding
    )

    renamer.process_directory(
        directory=directory,
        dry_run=args.dry_run,
        add_watermark=args.watermark,
        add_map=args.map,
        map_size=args.map_size,
        map_opacity=args.map_opacity,
        map_zoom=args.map_zoom,
        reprocess_map=args.reprocess_map,
        skip_processed=not args.no_skip,
        recursive=args.recursive,
        separator=args.separator
    )


if __name__ == '__main__':
    main()
