# 📸 GPS Photo Renamer

Automatisches Umbenennen von Fotos basierend auf GPS EXIF-Daten und Datum - mit nativer macOS Benutzeroberfläche.

[![Download](https://img.shields.io/badge/Download-Latest%20Release-blue?style=for-the-badge)](https://github.com/Stebibastian/gps-photo-renamer/releases/latest)
[![macOS](https://img.shields.io/badge/macOS-10.14+-000000?style=flat-square&logo=apple)](https://www.apple.com/macos/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## Features

- 🖥️ **Native macOS App** - Kein Terminal erforderlich
- ✨ **Smart Counter** - Nummerierung setzt automatisch fort
- 🌍 **GPS Geocoding** - Wandelt GPS-Koordinaten in Ortsnamen um
- 💧 **Wasserzeichen** - Datum (oben-links) und Ort (oben-rechts)
- 🧹 **macOS Cleanup** - Entfernt `.DS_Store` und `._*` Dateien automatisch

## Ausgabe-Format

```
Vorher: IMG_1234.JPG
Nachher: 20241226093045_0001_Graz_AT.jpg
```

## Installation

### Download (Empfohlen)

1. **[📥 Download GPS Photo Renamer (Latest)](https://github.com/Stebibastian/gps-photo-renamer/releases/latest)**
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
2. **Modus wählen** - Log-Vorschau oder direkt umbenennen
3. **Bestätigen** - Prüfen und starten
4. **Fertig** - Ordner öffnen oder nach Vorschau umbenennen

## Voraussetzungen

- macOS 10.14+
- Python 3 (auf macOS vorinstalliert)
- Internetverbindung (für GPS-Ortsabfrage)

Dependencies werden beim ersten Start automatisch installiert.

## Unterstützte Formate

- JPG / JPEG
- PNG
- HEIC / HEIF

## Problemlösung

### ⚠️ "App wurde blockiert"

**Lösung:** Systemeinstellungen → Datenschutz & Sicherheit → "Dennoch öffnen"

### ❌ Dependencies fehlen

Falls die automatische Installation fehlschlägt:
```bash
pip3 install Pillow requests --break-system-packages
```

### 📄 Log-Datei

Bei Problemen prüfe: `~/Desktop/gps_photo_renamer.log`

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

---

Made with ❤️ for organizing photo collections
