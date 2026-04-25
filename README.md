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
