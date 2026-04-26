# DDS Converter
> by DiccChops

A lightweight borderless GUI tool for converting game textures to **DirectX DDS format** on Windows.  
Wraps Microsoft's `texconv.exe` from the [DirectXTex](https://github.com/microsoft/DirectXTex) library.

---

## Features

- **Batch conversion** — convert an entire folder of images in one click
- **Single file conversion** — convert just one file straight from the queue
- **7 DDS formats** — DXT1, DXT3, DXT5, BC4\_UNORM, BC5\_UNORM, BC7\_UNORM, R8G8B8A8\_UNORM
- **Mipmap generation** — optional full mipmap chain for in-game use
- **Tint / Specular baking** — bake a colour tint into the texture before conversion
  - 5 blend modes: Multiply, Screen, Overlay, Add, Tint (Lerp)
  - Per-file or Apply to All
- **Live preview** — side-by-side Before / After panels with tint preview
- **Conversion log** — timestamped output for every file processed
- **4 built-in themes** — Dark, Light, Matrix, DarkBlueGrey — fully customisable per colour
- **Persistent settings** — theme and preferences saved to `dds_settings.json`

---

## Supported Input Formats

| Format | Extension |
|--------|-----------|
| PNG    | `.png`    |
| JPEG   | `.jpg` `.jpeg` |
| Targa  | `.tga`    |
| Bitmap | `.bmp`    |

**Output:** DirectX DDS — ready to drop into a game engine or 3D application

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| Windows     | Tested on Windows 10/11 |
| `texconv.exe` | Must be placed in the **same folder** as the app |
| Python 3.x  | Only needed if running from source |
| Pillow      | Only needed if running from source — `pip install Pillow` |

**Download `texconv.exe`:**  
?? https://github.com/microsoft/DirectXTex/releases

---

## Getting Started

### Option A — Pre-built (Recommended)
1. Download or build the `Image To DDS` folder (see [Building](#building))
2. Place `texconv.exe` inside the folder
3. Double-click `DDS Converter.exe`

### Option B — From Source
```bash
pip install Pillow
py DDS.py
```

---

## Building

A `build.bat` is included to package everything into a standalone `.exe` using PyInstaller.

```
Double-click build.bat
```

It will:
- Auto-install PyInstaller and Pillow if missing
- Build a single `DDS Converter.exe` (no console window)
- Create an `Image To DDS` folder containing everything needed
- Open the finished folder in Explorer

> **Note:** PyInstaller must be able to run via `py -m PyInstaller`. Python must be on your PATH.

---

## Project Structure

```
Img To DDS/
??? DDS.py              # Main application
??? build.bat           # Build script
??? info.txt            # In-app help content
??? DDSIcon.png         # App icon (PNG)
??? DDSIcon.ico         # App icon (ICO)
??? dds_settings.json   # Saved settings (auto-generated)
??? texconv.exe         # ? Not included — download separately
```

---

## DDS Format Guide

| Format | Alpha | Best For |
|--------|-------|----------|
| DXT1 | 1-bit / none | Opaque textures, smallest file size |
| DXT3 | Explicit | Sharp alpha edges |
| DXT5 | Smooth | Gradients, most common choice |
| BC4\_UNORM | — | Single-channel greyscale (R only) |
| BC5\_UNORM | — | Two-channel (R+G), normal maps |
| BC7\_UNORM | Full | High-quality RGBA, better than DXT5 |
| R8G8B8A8\_UNORM | Full | Uncompressed, no quality loss |

---

## License

Free to use, modify, and share — do whatever you want with it.  
**Just give credit: made by DiccChops.**

---

## Changelog

### v4.0
- App now launches fullscreen by default
- Maximize/restore button correctly reflects window state on startup
- Info window now opens centred over the main window instead of top-left
- Startup flash (white flicker) eliminated — window fades in invisibly during Win32 taskbar registration
- **?? OPEN** button added next to Output Folder to instantly open it in Explorer
- JPG Quality control is now hidden and only appears when JPG output is selected, with inline hint text (`100=lossless  95=high  85=web  75=small  60=low`)
- File queue `?` convert button is now always visible regardless of filename length (pack order fix)

### v3.0
- Added 7 output formats: DDS, PNG, JPG, TGA, BMP, WebP, SVG
- SVG output embeds the raster image as base64 PNG inside an SVG wrapper
- JPG quality spinbox added
- Per-file tint store — each file remembers its own colour, intensity, and blend mode
- **Apply to All** tint button
- 5 blend modes: Multiply, Screen, Overlay, Add, Tint (Lerp)
- Quick-pick colour swatches + custom colour picker
- Live Before / After preview panels with tint preview
- 4 built-in themes: Dark, Light, Matrix, DarkBlueGrey
- Full custom colour picker per UI element
- Settings saved to `dds_settings.json` (theme, folders, output type, quality)
- Crash log written to `dds_crash.log` next to the app

### v2.0
- Borderless custom title bar with drag, minimize, maximize/restore
- Scrollable file queue sidebar with per-file single-convert button
- Timestamped conversion log panel
- Progress bar with percentage label
- Stats bar: Total / Done / Fail / Tinted counters
- Win32 taskbar button registration for borderless window

### v1.0
- Initial release
- Batch DDS conversion via `texconv.exe`
- DXT1, DXT3, DXT5 format support
- Mipmap generation toggle