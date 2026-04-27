# Texture Pipeline Manager — v5.0
> by DiccChops

Professional texture pipeline manager for modders and technical artists. Designed for reliable batch processing, per-file tint/specular baking, and integration with external tooling such as Microsoft's `texconv` (DirectXTex).

This release (v5.0) focuses on workflow and scale: project files, folder templates, export manifests, parallelized conversion, and optional GPU-accelerated conversion via a compatible `texconv_gpu.exe` binary.

## Key capabilities

- Project system: save and load job configurations (folders, presets, per-file tints).
- Folder templates: quick project scaffolds for `Gear`, `UI`, `Vehicles`, `Weapons`.
- Export manifests: per-run JSON summary of converted files (format, size, status).
- Multi-threaded conversion with chunking and configurable worker count.
- Optional GPU-enabled conversion (place `texconv_gpu.exe` beside the app).
- Per-file tint/specular baking, live Before/After preview, and structured conversion logs (`dds_conversion.log`).

## Why use this tool

- Built for modders and small studios: manage texture conversion jobs, standardize outputs, and generate machine-readable manifests for downstream pipelines.
- Practical defaults (Auto DDS selection, PBR naming heuristics) plus advanced controls (format overrides, versioned outputs).
- Lightweight source (single-file) for inspection and extension, or packaged as a standalone Windows executable.

## Requirements

- Windows 10 / 11 (Win32 features used)
- `texconv.exe` (DirectXTex) — required for DDS output. For GPU acceleration, provide a compatible `texconv_gpu.exe` binary and enable GPU mode in the UI.
- Python 3.x + Pillow to run from source (or use the standalone executable built from this repo)

## Quick start

1. Place `texconv.exe` (or `texconv_gpu.exe`) in the same folder as the app.
2. Launch the app, apply a template or create a new project, set input/output folders.
3. Optionally save a project to reuse settings.
4. Configure `WORKERS` (1..16) and enable GPU if available, then START CONVERSION.

## Projects & templates

- Projects save the full job state as JSON (folders, preset, format, tints). Use SAVE / LOAD PROJECT in the toolbar.
- Templates create `projects/<template>_input` and `projects/<template>_output` under the app folder to bootstrap common workflows.

## Export manifest

- Each conversion run writes `export_manifest_YYYYMMDD_HHMMSS.json` into the output folder. Manifest entries include `file`, `status` (OK/SKIP/FAIL), `format`, `reason`, and `size` — suitable for automated importers or asset catalogs.

## Performance and scaling

- Increase `WORKERS` to parallelize conversions across CPU cores for large batches. The app uses chunking to reduce contention and memory pressure.
- Enable GPU if you have a compatible `texconv_gpu.exe` build for hardware-accelerated block compression.

## Supported Input / Output formats

Supported input: `.png`, `.jpg`, `.jpeg`, `.tga`, `.bmp`

Output formats: `DDS`, `PNG`, `JPG`, `TGA`, `BMP`, `WebP`, `SVG`.

When outputting `DDS`, formats supported include: `DXT1`, `DXT3`, `DXT5`, `BC4_UNORM`, `BC5_UNORM`, `BC7_UNORM`, `R8G8B8A8_UNORM` (UI/Modern choices exposed in the UI).

## Files of interest

- `DDS.py` — main application source (inspect or run directly with Python)
- `projects/` — sample templates and saved project JSON files
- `dds_conversion.log` — machine-friendly JSONL per-file log (appends during conversion)
- `export_manifest_*.json` — per-run manifest written into the output folder
- `dds_crash.log` — crash diagnostics

## Security & redistribution

- `texconv.exe` is not redistributed. Download it from Microsoft's DirectXTex releases and place it beside the app due to redistribution licensing.

## Support and contribution

Open issues and pull requests are welcome. Describe the target pipeline if you want custom template presets, CI-friendly manifest formats, or other integrations.

## Changelog

### v5.0
- Project system: save/load job configurations (folders, presets, per-file tints)
- Folder templates for Gear, UI, Vehicles, Weapons
- Export manifest JSON written to output folder per run
- Multi-threaded conversion with configurable worker count and chunking
- GPU toggle to use `texconv_gpu.exe` when present
- Structured per-file logging (JSONL) and improved error reasons

### v4.0
- App launched fullscreen by default; improved restore/maximize behaviour
- Info window centred; startup visual flicker eliminated
- Output folder OPEN button; improved JPG quality UI

For full history, inspect the repository tags and commit log.