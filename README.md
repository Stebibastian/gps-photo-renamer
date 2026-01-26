# 📸 GPS Photo Renamer

Automatisches Umbenennen von Fotos basierend auf GPS EXIF-Daten und Datum - mit nativer macOS Benutzeroberfläche.

[![Download](https://img.shields.io/badge/Download-v1.0.0-blue?style=for-the-badge)](https://github.com/Stebibastian/gps-photo-renamer/releases/latest)
[![macOS](https://img.shields.io/badge/macOS-10.14+-000000?style=flat-square&logo=apple)](https://www.apple.com/macos/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## Features

- 🖥️ **Native macOS App** - Kein Terminal erforderlich
- ✨ **Smart Counter** - Nummerierung setzt automatisch fort
- 🌍 **GPS Geocoding** - Wandelt GPS-Koordinaten in Ortsnamen um
- 💧 **Wasserzeichen** - Datum (oben-links) und Ort (oben-rechts)
- 🗺️ **Kartenausschnitt** - OpenStreetMap-Karte mit GPS-Position (15% vom Bild)
- 🎬 **Video-Erkennung** - Findet Videos und bietet Löschung an
- 🧹 **macOS Cleanup** - Entfernt `.DS_Store` und `._*` Dateien automatisch
- 📷 **Insta360 Support** - Fallback auf Datei-Datum wenn EXIF fehlt

## Screenshots

### Vorher → Nachher

| Original | Mit Wasserzeichen & Karte |
|----------|---------------------------|
| `IMG_1234.JPG` | `20260124125530_0001_MattenbeiInterlaken_CH_MAP.jpg` |

### Wasserzeichen-Layout

```
┌─────────────────────────────────────────┐
│ 24.01.2026          Matten bei Interlaken - CH │
│                              ┌────────┐ │
│                              │  🗺️   │ │
│                              │  MAP   │ │
│                              └────────┘ │
│                                         │
│              [ FOTO ]                   │
│                                         │
└─────────────────────────────────────────┘
```

## Installation

### Download (Empfohlen)

1. **[📥 Download GPS Photo Renamer v1.0.0](https://github.com/Stebibastian/gps-photo-renamer/releases/latest)**
2. ZIP-Datei entpacken
3. `GPS Photo Renamer.app` in den Programme-Ordner verschieben
4. Doppelklick zum Starten

**Erster Start - Sicherheitswarnung:**

macOS blockiert die App beim ersten Mal:
- Öffne **Systemeinstellungen** → **Datenschutz & Sicherheit**
- Scrolle zu: *"GPS Photo Renamer.app wurde blockiert"*
- Klicke **"Dennoch öffnen"** → **"Öffnen"** bestätigen

✅ Danach startet die App normal!

## Verwendung

1. **Ordner wählen** - Ordner mit Fotos auswählen
2. **Karte?** - Ja/Nein für Kartenausschnitt
3. **Karten-Einstellungen** - Standard oder Benutzerdefiniert (Grösse, Transparenz, Zoom)
4. **Modus wählen** - Log-Vorschau oder direkt umbenennen
5. **Fertig** - Fotos werden umbenannt mit Wasserzeichen

### Karten-Optionen

| Option | Klein | Standard | Gross |
|--------|-------|----------|-------|
| Grösse | 10% | 15% | 20% |
| Transparenz | 50% | 70% | 90% |
| Zoom | Strasse (15) | Stadtteil (13) | Region (11) |

## Voraussetzungen

- macOS 10.14+
- Python 3 (auf macOS vorinstalliert)
- Internetverbindung (für GPS-Ortsabfrage und Karten)

Dependencies werden beim ersten Start automatisch installiert.

## Unterstützte Formate

**Fotos:**
- JPG / JPEG
- PNG
- HEIC / HEIF

**Videos (werden erkannt, nicht umbenannt):**
- MP4, MOV, AVI, MKV, M4V
- 3GP, WebM
- INSV, LRV (Insta360, GoPro)

## Problemlösung

### ⚠️ "App wurde blockiert"

**Lösung:** Systemeinstellungen → Datenschutz & Sicherheit → "Dennoch öffnen"

### ❌ Dependencies fehlen

Falls die automatische Installation fehlschlägt:
```bash
pip3 install Pillow requests piexif --break-system-packages
```

### 📄 Log-Datei

Bei Problemen prüfe: `~/Desktop/gps_photo_renamer.log`

### 🗺️ Karte wird nicht angezeigt

- Internetverbindung prüfen (OpenStreetMap benötigt)
- Foto hat GPS-Daten (EXIF prüfen)

## Changelog

### v1.0.0 (2026-01-26)
- 🗺️ Kartenausschnitt mit OpenStreetMap
- 📍 Ortsnamen mit Leerzeichen korrekt angezeigt
- 📐 Proportionale Kartengrösse (% vom Bild)
- 🔧 Karten-Einstellungen (Grösse, Transparenz, Zoom)
- 🔄 Nachträgliches Hinzufügen von Karten zu bereits bearbeiteten Fotos

### v0.5.0
- Karten-Dialog und Reprocess-Option
- _MAP Tag im Dateinamen

### v0.4.0
- Video-Erkennung und Löschoption

### v0.3.0
- All-in-one App mit eingebettetem Python-Script

### v0.2.0
- Native macOS App mit UI

### v0.1.0
- Erste Version

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

---

Made with ❤️ by Stebibastian
