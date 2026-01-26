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
        return {
            'city': f"{lat:.5f}",
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
                    'city': self._clean_location_name(city),
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
                    'city': self._clean_location_name(city),
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
                    'city': self._clean_location_name(city),
                    'country_code': country_code
                }
        except Exception as e:
            print(f"  ⚠️  BigDataCloud error: {e}")
        return None
    
    def _clean_location_name(self, name: str) -> str:
        """Clean location name for use in filename."""
        # Remove special characters but keep umlauts
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with nothing or underscore
        name = name.replace(' ', '')
        return name
    
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
                               location: Optional[Dict] = None) -> bool:
        """
        Add watermark to image with date/time on left and location on right.
        Respects EXIF orientation to handle portrait/landscape correctly.

        Args:
            image_path: Path to image file
            datetime_str: Datetime string in format YYYYMMDDHHMMSS
            location: Dictionary with 'city' and 'country_code' keys

        Returns:
            True if watermark was added successfully
        """
        try:
            # Open image
            img = Image.open(image_path)

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
                right_text = f"{location['city']} - {location['country_code']}"
                
                # Get text bounding box
                bbox = draw.textbbox((0, 0), right_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Position (top right)
                x = img.size[0] - text_width - padding * 2
                y = padding
                
                # Background rectangle
                draw.rectangle(
                    [x - padding//2, y - padding//2,
                     x + text_width + padding//2, y + text_height + padding//2],
                    fill=(0, 0, 0, 180)
                )
                
                # Text
                draw.text((x, y), right_text, font=font, fill=(255, 255, 255, 255))
            
            # Composite
            img = Image.alpha_composite(img, overlay)
            
            # Convert back to RGB and save
            img = img.convert('RGB')
            img.save(image_path, quality=95)
            
            return True
            
        except Exception as e:
            print(f"  ⚠️  Watermark error: {e}")
            return False
    
    def is_already_processed(self, filename: str) -> bool:
        """
        Check if filename matches the pattern of already processed files.
        Pattern: YYYYMMDDHHMMSS_NNNN[_Location_CC].ext
        """
        # Pattern: starts with 12-14 digits, underscore, 4 digits
        pattern = r'^\d{12,14}_\d{4}'
        return bool(re.match(pattern, filename))
    
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
                         add_watermark: bool = False, skip_processed: bool = True,
                         recursive: bool = False, separator: str = '_'):
        """
        Process all photos in directory.
        
        Args:
            directory: Directory containing photos
            dry_run: If True, only show what would be renamed
            add_watermark: If True, add watermark to images
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
        
        for idx, photo_path in enumerate(photo_files, 1):
            print(f"\n[{idx}/{len(photo_files)}] Processing: {photo_path.name}")

            # Check if already processed
            if skip_processed and self.is_already_processed(photo_path.name):
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
                new_name = f"{base_name}{separator}{city}{separator}{country}{photo_path.suffix}"
            else:
                new_name = f"{base_name}{photo_path.suffix}"
            
            new_path = photo_path.parent / new_name
            
            # Rename file
            if not dry_run:
                try:
                    photo_path.rename(new_path)
                    print(f"  ✓ {photo_path.name}")
                    print(f"    → {new_name}")
                    
                    # Add watermark if requested
                    if add_watermark:
                        self.add_watermark_to_image(new_path, datetime_str, location)
                    
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
        skip_processed=not args.no_skip,
        recursive=args.recursive,
        separator=args.separator
    )


if __name__ == '__main__':
    main()
