import base64
import sys, traceback, os
try:
    import faulthandler
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd(), 'texforge_crash.log')
        faulthandler.enable(file=open(log_path, 'a'))
    except Exception:
        faulthandler.enable()
except Exception:
    pass
try:
    import json
    import subprocess
    import tempfile
    import threading
    from io import BytesIO
    import tkinter as tk
    from tkinter import filedialog, ttk, messagebox, colorchooser
    from PIL import Image, ImageTk, ImageChops
    from datetime import datetime
except Exception:
    tb = traceback.format_exc()
    print(tb, file=sys.stderr, flush=True)
    try:
        # best-effort write to crash log next to this script
        app_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
        crash_log = os.path.join(app_dir, "texforge_crash.log")
        with open(crash_log, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n{tb}")
    except Exception:
        pass
    raise

# ── Resolve app directory safely for both script and frozen exe ──
# sys.executable points to the .exe when frozen; __file__ may not exist.
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# CONFIG
# =========================
TEXCONV_PATH     = "texconv.exe"
VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tga", ".bmp")

COLORS = {
    "bg":       "#141414",
    "panel":    "#1c1c1c",
    "sidebar":  "#181818",
    "border":   "#2a2a2a",
    "accent":   "#00e87a",
    "accent2":  "#0096ff",
    "warn":     "#ffaa00",
    "error":    "#ff4444",
    "text":     "#e0e0e0",
    "subtext":  "#888888",
    "input_bg": "#222222",
    "done":     "#00e87a",
    "fail":     "#ff4444",
    "info":     "#0096ff",
}

FONT_MONO  = ("Consolas", 9)
FONT_UI    = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 8, "bold")
FONT_STAT  = ("Consolas", 12, "bold")

# Quick-pick swatches  (label, hex or None = clear)
SWATCHES = [
    ("✖",       None),
    ("Yellow",  "#FFDD00"),
    ("Orange",  "#FF8800"),
    ("Red",     "#FF2222"),
    ("Pink",    "#FF55CC"),
    ("Violet",  "#AA44FF"),
    ("Blue",    "#2288FF"),
    ("Cyan",    "#00DDFF"),
    ("Green",   "#33EE66"),
    ("Gold",    "#FFD700"),
    ("Silver",  "#C0C0C0"),
    ("White",   "#FFFFFF"),
]

BLEND_MODES = ["Multiply", "Screen", "Overlay", "Add", "Tint (Lerp)"]

OUTPUT_FORMATS = ["DDS", "PNG", "JPG", "TGA", "BMP", "WebP", "SVG"]

# Preset profiles for common engine targets
PRESET_NAMES = [
    "(none)",
    "🎮 FiveM / GTA V",
    "🎮 Skyrim / Fallout",
    "🎮 Unity textures",
    "🎮 Unreal Engine",
    "🧱 UI Icons / 2D sprites",
    "🧊 PBR materials (metal/rough/normal maps)",
]

# Mapping preset -> config (dds_mode label, format, mipmaps)
PRESETS = {
    "(none)": {},
    "🎮 FiveM / GTA V": {"dds_mode": "Legacy (Game compatible)", "format": "DXT5", "mips": True},
    "🎮 Skyrim / Fallout": {"dds_mode": "Legacy (Game compatible)", "format": "Auto", "mips": True},
    "🎮 Unity textures": {"dds_mode": "Modern (DX10/DXGI)", "format": "BC7_UNORM", "mips": True},
    "🎮 Unreal Engine": {"dds_mode": "Modern (DX10/DXGI)", "format": "BC7_UNORM", "mips": True},
    "🧱 UI Icons / 2D sprites": {"dds_mode": "Auto (detect alpha)", "format": "Auto", "mips": False},
    "🧊 PBR materials (metal/rough/normal maps)": {"dds_mode": "Modern (DX10/DXGI)", "format": "BC7_UNORM", "mips": True, "pbr_rules": True},
}

SETTINGS_FILE = os.path.join(APP_DIR, "texforge_settings.json")
CRASH_LOG     = os.path.join(APP_DIR, "texforge_crash.log")
STRUCT_LOG    = os.path.join(APP_DIR, "texforge_conversion.log")
PROJECTS_DIR  = os.path.join(APP_DIR, "projects")

# Folder templates for quick project setup
FOLDER_TEMPLATES = {
    "Gear":     {"input_sub": "gear_input",     "output_sub": "gear_output",     "preset": "🎮 FiveM / GTA V"},
    "UI":       {"input_sub": "ui_input",       "output_sub": "ui_output",       "preset": "🧱 UI Icons / 2D sprites"},
    "Vehicles": {"input_sub": "vehicles_input", "output_sub": "vehicles_output", "preset": "🎮 FiveM / GTA V"},
    "Weapons":  {"input_sub": "weapons_input",  "output_sub": "weapons_output",  "preset": "🎮 FiveM / GTA V"},
}

THEMES = {
    "Dark": {
        "bg": "#141414", "panel": "#1c1c1c", "sidebar": "#181818",
        "border": "#2a2a2a", "accent": "#00e87a", "accent2": "#0096ff",
        "warn": "#ffaa00", "error": "#ff4444", "text": "#e0e0e0",
        "subtext": "#888888", "input_bg": "#222222", "done": "#00e87a",
        "fail": "#ff4444", "info": "#0096ff",
    },
    "Light": {
        "bg": "#f5f5f5", "panel": "#e8e8e8", "sidebar": "#ebebeb",
        "border": "#cccccc", "accent": "#00995a", "accent2": "#0077dd",
        "warn": "#cc7700", "error": "#cc2222", "text": "#1a1a1a",
        "subtext": "#666666", "input_bg": "#ffffff", "done": "#00995a",
        "fail": "#cc2222", "info": "#0077dd",
    },
    "Matrix": {
        "bg": "#000000", "panel": "#001100", "sidebar": "#000d00",
        "border": "#003300", "accent": "#00ff41", "accent2": "#00cc33",
        "warn": "#aaff00", "error": "#ff3300", "text": "#00dd33",
        "subtext": "#005500", "input_bg": "#001a00", "done": "#00ff41",
        "fail": "#ff3300", "info": "#00cc33",
    },
    "DarkBlueGrey": {
        "bg": "#1e2124", "panel": "#282b30", "sidebar": "#2f3136",
        "border": "#40444b", "accent": "#7289da", "accent2": "#43b581",
        "warn": "#faa61a", "error": "#f04747", "text": "#dcddde",
        "subtext": "#72767d", "input_bg": "#36393f", "done": "#43b581",
        "fail": "#f04747", "info": "#7289da",
    },
}


# =========================
# TINT ENGINE
# =========================
def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _overlay_fallback(src: Image.Image, solid: Image.Image) -> Image.Image:
    """Manual overlay blend for Pillow < 9.2 that lacks ImageChops.overlay."""
    import struct
    src_r  = src.split()
    sol_r  = solid.split()
    bands  = []
    for s_band, o_band in zip(src_r, sol_r):
        s = s_band.tobytes()
        o = o_band.tobytes()
        result = bytearray(len(s))
        for i, (sv, ov) in enumerate(zip(s, o)):
            sf, of = sv / 255.0, ov / 255.0
            if sf < 0.5:
                rf = 2 * sf * of
            else:
                rf = 1 - 2 * (1 - sf) * (1 - of)
            result[i] = int(rf * 255)
        bands.append(Image.frombytes("L", s_band.size, bytes(result)))
    return Image.merge(src.mode, bands)


def apply_tint(img: Image.Image, hex_color: str, intensity: float, mode: str) -> Image.Image:
    if intensity <= 0 or not hex_color:
        return img
    r, g, b   = hex_to_rgb(hex_color)
    src       = img.convert("RGBA")
    solid     = Image.new("RGBA", src.size, (r, g, b, 255))
    solid_a   = Image.new("RGBA", src.size, (r, g, b, int(255 * intensity)))

    if mode == "Multiply":
        blended = ImageChops.multiply(src, solid)
        result  = Image.blend(src, blended, intensity)
    elif mode == "Screen":
        blended = ImageChops.screen(src, solid)
        result  = Image.blend(src, blended, intensity)
    elif mode == "Overlay":
        try:
            blended = ImageChops.overlay(src, solid)
        except AttributeError:
            # Pillow < 9.2 — use manual fallback
            blended = _overlay_fallback(src, solid)
        result = Image.blend(src, blended, intensity)
    elif mode == "Add":
        result = ImageChops.add(src, solid_a, scale=1.0, offset=0)
    else:  # Tint (Lerp)
        result = Image.blend(src, solid, intensity)

    return result.convert(img.mode if img.mode in ("RGB", "RGBA") else "RGBA")


def luminance(hex_color: str) -> float:
    r, g, b = hex_to_rgb(hex_color)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def save_as_svg(img: Image.Image, dst_path: str):
    """Embed a raster image as base64 PNG inside an SVG wrapper."""
    w, h = img.size
    buf  = BytesIO()
    save_img = img if img.mode in ("RGB", "RGBA") else img.convert("RGBA")
    save_img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        f'  <image xlink:href="data:image/png;base64,{b64}" '
        f'x="0" y="0" width="{w}" height="{h}"/>\n'
        f'</svg>\n'
    )
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(svg)


# =========================
# TOOLTIP
# =========================
class _Tooltip:
    """Lightweight delayed hover tooltip for any tkinter widget."""
    _DELAY_MS = 480

    def __init__(self, widget, text: str):
        self._widget = widget
        self._text   = text
        self._win    = None
        self._after  = None
        widget.bind("<Enter>",       self._schedule, add="+")
        widget.bind("<Leave>",       self._cancel,   add="+")
        widget.bind("<ButtonPress>", self._cancel,   add="+")

    def _schedule(self, event=None):
        self._cancel()
        self._after = self._widget.after(self._DELAY_MS, self._show)

    def _cancel(self, event=None):
        if self._after:
            self._widget.after_cancel(self._after)
            self._after = None
        if self._win:
            self._win.destroy()
            self._win = None

    def _show(self):
        if self._win:
            return
        try:
            x = self._widget.winfo_rootx() + 16
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
            self._win = tw = tk.Toplevel(self._widget)
            tw.overrideredirect(True)
            tw.attributes("-topmost", True)
            tw.geometry(f"+{x}+{y}")
            tk.Label(tw, text=self._text, justify="left",
                     bg=COLORS["panel"], fg=COLORS["text"],
                     font=("Segoe UI", 8), relief="flat",
                     padx=9, pady=5, wraplength=320).pack()
            tw.config(highlightbackground=COLORS["border"], highlightthickness=1)
        except Exception:
            self._win = None


# =========================
# APP
# =========================
class DDSConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg=COLORS["bg"])

        # Start fullscreen
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        w, h = sw, sh
        x, y = 0, 0
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(1100, 660)
        self.root.overrideredirect(True)
        self._maximized = True

        # Load window icon
        self._icon_photo_small = None
        try:
            _ico = Image.open(os.path.join(APP_DIR, "DDSIcon.png"))
            self._icon_photo_small = ImageTk.PhotoImage(_ico.resize((16, 16), Image.LANCZOS))
            self.root.iconphoto(True, ImageTk.PhotoImage(_ico))
        except Exception:
            pass

        # Drag / maximize state
        self._drag_x = self._drag_y = 0
        self._restore_geo = f"1340x800+{(sw-1340)//2}+{(sh-800)//2}"

        # Theme
        self._current_theme = "Dark"

        self.input_folder  = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.format        = tk.StringVar(value="DXT5")
        # DDS output mode: Legacy (DXT), Modern (DX10/DXGI), or Auto (detect alpha -> DXT1/DXT5)
        self.dds_mode       = tk.StringVar(value="Auto")
        self.preset         = tk.StringVar(value="(none)")
        self.overwrite_mode  = tk.StringVar(value="Never")
        self.watch_mode      = tk.BooleanVar(value=False)
        # internals for watch/queue
        self._watched_files = set()
        self._pending_watch_files = []
        self.output_type   = tk.StringVar(value="DDS")
        self.mip_maps      = tk.BooleanVar(value=True)
        self.jpeg_quality  = tk.IntVar(value=90)

        # tint per-file store
        self._file_tints: dict = {}          # fname → {color, intensity, mode}
        self._file_formats: dict = {}        # fname → DDS format override ("" = global)
        self._rename_prefix = tk.StringVar(value="")
        self._rename_suffix = tk.StringVar(value="")
        self._tint_color     = tk.StringVar(value="")
        self._tint_intensity = tk.DoubleVar(value=40.0)
        self._tint_mode      = tk.StringVar(value="Multiply")
        self._selected_file  = None

        # Preview system state
        self._preview_zoom = tk.StringVar(value="Fit")
        self._preview_checker = tk.BooleanVar(value=True)
        self._preview_mip_level = tk.IntVar(value=0)
        self._preview_src_img = None
        self._preview_after_img = None

        self._converting = False
        self._show_info_on_start = True

        # Route all unhandled exceptions to console + crash log
        sys.excepthook = self._on_exception
        self.root.report_callback_exception = self._on_tk_exception

        self._load_settings()
        self._build_styles()
        self._build_ui()
        self.root.after(100, self._apply_win32_style)
        self.root.after(350, self._maybe_show_info)
        if self.input_folder.get():
            self.root.after(50, self.load_files)

    # ─────────────────────────────────────────
    # STYLES
    # ─────────────────────────────────────────
    def _build_styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TProgressbar",
                    troughcolor=COLORS["border"], background=COLORS["accent"],
                    bordercolor=COLORS["border"], lightcolor=COLORS["accent"],
                    darkcolor=COLORS["accent"], thickness=6)
        s.configure("TCombobox",
                    fieldbackground=COLORS["input_bg"], background=COLORS["input_bg"],
                    foreground=COLORS["text"], selectbackground=COLORS["accent"],
                    selectforeground="#000")
        s.map("TCombobox", fieldbackground=[("readonly", COLORS["input_bg"])])

    # ─────────────────────────────────────────
    # EXCEPTION LOGGING
    # ─────────────────────────────────────────
    def _on_exception(self, exc_type, exc_value, exc_tb):
        self._write_crash(exc_type, exc_value, exc_tb)

    def _on_tk_exception(self, exc_type, exc_value, exc_tb):
        self._write_crash(exc_type, exc_value, exc_tb)

    def _write_crash(self, exc_type, exc_value, exc_tb):
        lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        msg   = "".join(lines)
        print(msg, file=sys.stderr, flush=True)
        try:
            with open(CRASH_LOG, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n{datetime.now():%Y-%m-%d %H:%M:%S}\n{msg}")
        except Exception:
            pass

    def _log_file_status(self, status: str, filename: str, reason: str = "", fmt: str = ""):
        """Structured per-file logging: write human-readable line to UI log and append JSONL to `STRUCT_LOG`.

        status: one of 'OK','SKIP','FAIL'
        filename: basename or relative path shown to user
        reason: short error / note string
        fmt: format or codec used (e.g. 'DXT5')
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # build readable line
        line = f"[{status}] {filename}"
        if fmt:
            line += f" → {fmt}"
        if reason:
            line += f"  •  {reason}"

        # map status to existing UI tags
        tag = "done" if status == "OK" else ("sub" if status == "SKIP" else "fail")
        # keep a compact log entry in the UI
        self._log(tag, line)

        # append structured JSON line to disk
        try:
            rec = {"timestamp": ts, "file": filename, "status": status, "format": fmt, "reason": reason}
            with open(STRUCT_LOG, "a", encoding="utf-8") as fh:
                json.dump(rec, fh, ensure_ascii=False)
                fh.write("\n")
        except Exception:
            # never fail the app for logging problems
            pass

    # ─────────────────────────────────────────
    # WIN32 TASKBAR
    # ─────────────────────────────────────────
    def _apply_win32_style(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            GWL_EXSTYLE      = -20
            WS_EX_APPWINDOW  = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            self.root.update_idletasks()
            # swap toolwindow -> appwindow so overrideredirect windows appear in taskbar
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            # force the shell to pick up the style change
            self.root.withdraw()
            self.root.after(10, self.root.deiconify)
        except Exception:
            pass

    # ─────────────────────────────────────────
    # PREVIEW RENDERING
    # ─────────────────────────────────────────
    def _update_mip_slider(self, img: Image.Image):
        if img is None:
            self._mip_slider.config(from_=0, to=0)
            self._preview_mip_level.set(0)
            self._mip_label.config(text="0")
            return
        w, h = img.size
        maxdim = max(w, h)
        import math
        levels = max(1, int(math.floor(math.log2(maxdim))) + 1)
        # allow levels-1 as max index
        self._mip_slider.config(from_=0, to=max(0, levels-1))
        if self._preview_mip_level.get() > max(0, levels-1):
            self._preview_mip_level.set(max(0, levels-1))
        self._mip_label.config(text=str(self._preview_mip_level.get()))

    def _on_preview_change(self):
        # refresh both previews if present
        try:
            if self._preview_src_img is not None:
                self._render_preview(self._preview_src_img, self.before_frame)
            if self._preview_after_img is not None:
                self._render_preview(self._preview_after_img, self.after_frame)
            self._mip_label.config(text=str(self._preview_mip_level.get()))
        except Exception:
            pass

    def _render_preview(self, img: Image.Image, box, size_bytes=0):
        if img is None:
            self._clear_preview(box, "no preview")
            return
        try:
            # pick mip level
            level = int(self._preview_mip_level.get())
            if level > 0:
                w, h = img.size
                nw = max(1, w // (2 ** level))
                nh = max(1, h // (2 ** level))
                img_disp = img.copy().resize((nw, nh), resample=Image.LANCZOS)
            else:
                img_disp = img.copy()

            # checkerboard if requested and image has alpha
            if self._preview_checker.get() and "A" in img_disp.getbands():
                base = Image.new("RGBA", img_disp.size)
                # create checker pattern
                tile = 8
                c1 = (200, 200, 200, 255)
                c2 = (120, 120, 120, 255)
                bx, by = img_disp.size
                checker = Image.new("RGBA", img_disp.size, c1)
                tile_img = Image.new("RGBA", (tile, tile), c2)
                for y in range(0, by, tile):
                    for x in range(0, bx, tile):
                        if ((x//tile) + (y//tile)) % 2 == 0:
                            checker.paste(tile_img, (x, y))
                base.paste(checker, (0,0))
                base.paste(img_disp, (0,0), img_disp)
                img_disp = base.convert("RGBA")
            else:
                # ensure no alpha shown as solid if checker off
                if img_disp.mode in ("RGBA", "LA"):
                    img_disp = img_disp.convert("RGBA")
                else:
                    img_disp = img_disp.convert("RGB")

            # zoom
            z = self._preview_zoom.get()
            if z == "Fit":
                # try to fit into label size, fallback to 320x260
                lbl = box._img_label
                w = lbl.winfo_width() or 320
                h = lbl.winfo_height() or 260
                img_fit = img_disp.copy()
                img_fit.thumbnail((w-8, h-8), Image.LANCZOS)
                out_img = img_fit
            else:
                pct = int(z.replace('%','')) if '%' in z else int(z)
                factor = pct / 100.0
                ow, oh = img_disp.size
                out_img = img_disp.copy().resize((max(1,int(ow*factor)), max(1,int(oh*factor))), Image.LANCZOS)

            photo = ImageTk.PhotoImage(out_img)
            box._img_label.config(image=photo, text="")
            box._img_label._photo = photo
            box._info_label.config(text=f"{img.size[0]}×{img.size[1]}px  •  {size_bytes/1024:.1f} KB  •  {img.mode}  •  MIP {level}")
        except Exception as e:
            # render error in preview and log
            box._img_label.config(image="", text=f"⚠ {e}", fg=COLORS['warn'], compound='center')
            self._log("warn", f"Preview error: {e}")

    # ─────────────────────────────────────────
    # INFO WINDOW
    # ─────────────────────────────────────────
    def _maybe_show_info(self):
        if self._show_info_on_start:
            self._open_info_window()

    def _open_info_window(self):
        if hasattr(self, "_info_win") and self._info_win.winfo_exists():
            self._info_win.lift()
            return

        win = tk.Toplevel(self.root)
        self._info_win = win
        win.configure(bg=COLORS["bg"])
        win.overrideredirect(True)
        win.grab_set()

        iw, ih = 560, 520
        rx = self.root.winfo_x() + (self.root.winfo_width()  - iw) // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() - ih) // 2
        win.geometry(f"{iw}x{ih}+{rx}+{ry}")
        win.resizable(False, True)

        # Custom title bar
        hdr = tk.Frame(win, bg=COLORS["panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="ℹ  TexForge — INFO",
                 fg=COLORS["info"], bg=COLORS["panel"],
                 font=("Consolas", 11, "bold")).pack(side="left", padx=14, pady=10)
        tk.Button(hdr, text=" ✕ ", bg=COLORS["panel"], fg=COLORS["text"],
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  activebackground=COLORS["error"], activeforeground="#fff",
                  cursor="hand2", bd=0, command=win.destroy).pack(side="right")
        tk.Frame(win, bg=COLORS["border"], height=1).pack(fill="x")

        # Drag support
        _drag = {"x": 0, "y": 0}
        def _press(e): _drag["x"] = e.x_root - win.winfo_x(); _drag["y"] = e.y_root - win.winfo_y()
        def _move(e):  win.geometry(f"+{e.x_root - _drag['x']}+{e.y_root - _drag['y']}")
        for _w in [hdr] + [c for c in hdr.winfo_children() if isinstance(c, tk.Label)]:
            _w.bind("<ButtonPress-1>", _press)
            _w.bind("<B1-Motion>",     _move)

        body = tk.Frame(win, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)
        txt = tk.Text(body, bg=COLORS["input_bg"], fg=COLORS["text"],
                      font=("Consolas", 9), relief="flat", bd=10,
                      wrap="word", state="normal", cursor="arrow")
        txt.pack(fill="both", expand=True)
        txt.bind("<MouseWheel>", lambda e: txt.yview_scroll(-1*(e.delta//120), "units"))

        try:
            _candidates = [
                os.path.join(APP_DIR, "info.txt"),
                os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "info.txt"),
                os.path.join(os.getcwd(), "info.txt"),
            ]
            content = None
            for _p in _candidates:
                if os.path.isfile(_p):
                    with open(_p, encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    break
            if content is None:
                content = "info.txt not found next to the executable."
        except Exception:
            content = "info.txt could not be loaded."

        txt.tag_config("heading",   foreground=COLORS["accent"],  font=("Consolas", 11, "bold"))
        txt.tag_config("section",   foreground=COLORS["accent2"], font=("Consolas",  9, "bold"))
        txt.tag_config("warn_line", foreground=COLORS["warn"],    font=("Consolas",  9))
        txt.tag_config("good_line", foreground=COLORS["done"],    font=("Consolas",  9))
        txt.tag_config("dim_line",  foreground=COLORS["subtext"], font=("Consolas",  9))
        txt.tag_config("sep",       foreground=COLORS["accent"],  font=("Consolas",  9, "bold"))
        txt.tag_config("indent",    foreground=COLORS["subtext"], font=("Consolas",  9))
        txt.tag_config("body",      foreground=COLORS["text"],    font=("Consolas",  9))

        def _insert_markup(text_widget, raw):
            for line in raw.splitlines(keepends=True):
                stripped = line.rstrip("\n")
                if stripped.startswith("## "):
                    text_widget.insert(tk.END, stripped[3:] + "\n", "heading")
                elif stripped.startswith("# "):
                    text_widget.insert(tk.END, stripped[2:] + "\n", "section")
                elif stripped.startswith("! "):
                    text_widget.insert(tk.END, stripped[2:] + "\n", "warn_line")
                elif stripped.startswith("+ "):
                    text_widget.insert(tk.END, stripped[2:] + "\n", "good_line")
                elif stripped.startswith("~ "):
                    text_widget.insert(tk.END, stripped[2:] + "\n", "dim_line")
                elif stripped.startswith("==="):
                    text_widget.insert(tk.END, stripped + "\n", "sep")
                elif len(stripped) > 0 and stripped[0] in (" ", "\t"):
                    text_widget.insert(tk.END, stripped + "\n", "indent")
                else:
                    text_widget.insert(tk.END, stripped + "\n", "body")

        _insert_markup(txt, content)
        txt.config(state="disabled")

        # Footer
        tk.Frame(win, bg=COLORS["border"], height=1).pack(fill="x")
        footer = tk.Frame(win, bg=COLORS["panel"])
        footer.pack(fill="x", pady=6)

        startup_var = tk.BooleanVar(value=self._show_info_on_start)
        def _on_toggle():
            self._show_info_on_start = startup_var.get()
            self._save_settings()
        tk.Checkbutton(footer, text="Show this on startup",
                       variable=startup_var, command=_on_toggle,
                       fg=COLORS["text"], bg=COLORS["panel"],
                       selectcolor=COLORS["input_bg"],
                       activeforeground=COLORS["accent"],
                       activebackground=COLORS["panel"],
                       font=FONT_UI).pack(side="left", padx=14)
        tk.Button(footer, text="✕  CLOSE", bg=COLORS["border"], fg=COLORS["warn"],
                  relief="flat", font=FONT_TITLE, padx=12, pady=4,
                  cursor="hand2", command=win.destroy).pack(side="right", padx=10)

    # ─────────────────────────────────────────
    # TITLEBAR
    # ─────────────────────────────────────────
    def _build_titlebar(self):
        tb = tk.Frame(self.root, bg=COLORS["panel"], height=34)
        tb.pack(fill="x")
        tb.pack_propagate(False)

        if self._icon_photo_small:
            tk.Label(tb, image=self._icon_photo_small,
                     bg=COLORS["panel"]).pack(side="left", padx=(10, 4), pady=9)

        tk.Label(tb, text="TexForge by DiccChops", fg=COLORS["accent"],
                 bg=COLORS["panel"], font=("Consolas", 11, "bold")).pack(side="left", padx=(2, 6))
        tk.Label(tb, text="[ multi-format texture pipeline ]",
                 fg=COLORS["subtext"], bg=COLORS["panel"], font=FONT_MONO).pack(side="left")

        _close_btn = tk.Button(tb, text=" ✕ ", bg=COLORS["panel"], fg=COLORS["text"],
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  activebackground=COLORS["error"], activeforeground="#fff",
                  cursor="hand2", bd=0,
                  command=self.root.destroy)
        _close_btn.pack(side="right")
        self._tip(_close_btn, "Close the application")
        self._max_btn = tk.Button(tb, text=" ❐ " if self._maximized else " □ ",
                  bg=COLORS["panel"], fg=COLORS["text"],
                  relief="flat", font=("Segoe UI", 10),
                  activebackground=COLORS["border"], activeforeground=COLORS["text"],
                  cursor="hand2", bd=0,
                  command=self._toggle_maximize)
        self._max_btn.pack(side="right")
        self._tip(self._max_btn, "Maximize / restore window")
        _min_btn = tk.Button(tb, text=" ─ ", bg=COLORS["panel"], fg=COLORS["text"],
                  relief="flat", font=("Segoe UI", 10),
                  activebackground=COLORS["border"], activeforeground=COLORS["text"],
                  cursor="hand2", bd=0,
                  command=self._minimize)
        _min_btn.pack(side="right")
        self._tip(_min_btn, "Minimize to taskbar")

        tk.Label(tb, text=" v7.0 ", fg="#000", bg=COLORS["accent"],
                 font=("Consolas", 7, "bold")).pack(side="right", padx=(0, 6), pady=9)

        _info_btn = tk.Button(tb, text=" ℹ ", bg=COLORS["info"], fg="#fff",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  activebackground=COLORS["accent2"], activeforeground="#fff",
                  cursor="hand2", bd=0,
                  command=self._open_info_window)
        _info_btn.pack(side="right", padx=(0, 2))
        self._tip(_info_btn, "Open the help / info window")
        _cfg_btn = tk.Button(tb, text=" ⚙ ", bg=COLORS["panel"], fg=COLORS["subtext"],
                  relief="flat", font=("Segoe UI", 10),
                  activebackground=COLORS["border"], activeforeground=COLORS["accent"],
                  cursor="hand2", bd=0,
                  command=self._open_settings)
        _cfg_btn.pack(side="right", padx=(0, 4))
        self._tip(_cfg_btn, "Open theme and colour settings")

        for w in [tb] + [c for c in tb.winfo_children() if isinstance(c, tk.Label)]:
            w.bind("<ButtonPress-1>",   self._titlebar_press)
            w.bind("<B1-Motion>",       self._titlebar_drag)
            w.bind("<Double-Button-1>", lambda e: self._toggle_maximize())

        tk.Frame(self.root, bg=COLORS["border"], height=1).pack(fill="x")

    def _titlebar_press(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _titlebar_drag(self, event):
        if self._maximized:
            self._toggle_maximize()
            self._drag_x = self.root.winfo_width() // 2
            self._drag_y = 17
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def _toggle_maximize(self):
        if self._maximized:
            self.root.geometry(self._restore_geo)
            self._max_btn.config(text=" □ ")
            self._maximized = False
        else:
            self._restore_geo = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
            self._max_btn.config(text=" ❐ ")
            self._maximized = True

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.update_idletasks()
        self.root.iconify()
        self.root.bind("<Map>", self._on_map)

    def _on_map(self, event):
        self.root.unbind("<Map>")
        self.root.after(50, self._restore_chrome)

    def _restore_chrome(self):
        try:
            if self.root.state() == "normal":
                self.root.overrideredirect(True)
                self.root.lift()
                self.root.after(100, self._apply_win32_style)
            else:
                self.root.after(50, self._restore_chrome)
        except Exception:
            self._write_crash(*sys.exc_info())

    # ─────────────────────────────────────────
    # SETTINGS
    # ─────────────────────────────────────────
    def _load_settings(self):
        global COLORS
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            if "colors" in data:
                COLORS.update(data["colors"])
            if "theme" in data:
                self._current_theme = data["theme"]
            if "show_info_on_start" in data:
                self._show_info_on_start = data["show_info_on_start"]
            if "output_type" in data:
                self.output_type.set(data["output_type"])
            if "jpeg_quality" in data:
                self.jpeg_quality.set(int(data["jpeg_quality"]))
            if "dds_mode" in data:
                # tolerate older simple values as well as full labels
                self.dds_mode.set(data["dds_mode"])
            if "preset" in data:
                self.preset.set(data["preset"])
            if data.get("input_folder") and os.path.isdir(data["input_folder"]):
                self.input_folder.set(data["input_folder"])
            if data.get("output_folder"):
                self.output_folder.set(data["output_folder"])
            if "overwrite_mode" in data:
                self.overwrite_mode.set(data["overwrite_mode"])
            if "watch_mode" in data:
                self.watch_mode.set(bool(data["watch_mode"]))
            if "workers" in data:
                try: self._workers.set(int(data.get("workers", 1)))
                except Exception: pass
            if "use_gpu" in data:
                try: self._use_gpu.set(bool(data.get("use_gpu", False)))
                except Exception: pass
            if "rename_prefix" in data:
                self._rename_prefix.set(data.get("rename_prefix", ""))
            if "rename_suffix" in data:
                self._rename_suffix.set(data.get("rename_suffix", ""))
        except Exception:
            pass

    def _save_settings(self, silent=False):
        data = {"theme": self._current_theme, "colors": dict(COLORS),
                "show_info_on_start": self._show_info_on_start,
                "output_type": self.output_type.get(),
                "dds_mode": self.dds_mode.get(),
                "preset": self.preset.get(),
                "overwrite_mode": self.overwrite_mode.get(),
                "watch_mode": bool(self.watch_mode.get()),
                "jpeg_quality": self.jpeg_quality.get(),
                "workers": int(self._workers.get()),
                "use_gpu": bool(self._use_gpu.get()),
                "rename_prefix": self._rename_prefix.get(),
                "rename_suffix": self._rename_suffix.get(),
                "input_folder": self.input_folder.get(),
                "output_folder": self.output_folder.get()}
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
            if not silent and hasattr(self, "_settings_win") and self._settings_win.winfo_exists():
                messagebox.showinfo("Saved", "Settings saved as default.",
                                    parent=self._settings_win)
        except Exception as e:
            self._log("warn", f"Could not save settings: {e}")

    def _apply_theme(self, theme_name):
        global COLORS
        COLORS.update(THEMES[theme_name])
        self._current_theme = theme_name
        self._apply_theme_colors()

    def _apply_theme_colors(self):
        if hasattr(self, "_settings_win") and self._settings_win.winfo_exists():
            self._settings_win.destroy()
        for w in self.root.winfo_children():
            if not isinstance(w, tk.Toplevel):
                w.destroy()
        self._build_styles()
        self._build_ui()
        if self.input_folder.get():
            self.load_files()

    def _pick_color_setting(self, key):
        result = colorchooser.askcolor(color=COLORS[key], title=f"Pick colour — {key}")
        if result and result[1]:
            COLORS[key] = result[1].upper()
            self._apply_theme_colors()

    def _open_settings(self):
        if hasattr(self, "_settings_win") and self._settings_win.winfo_exists():
            self._settings_win.lift()
            return

        win = tk.Toplevel(self.root)
        self._settings_win = win
        win.configure(bg=COLORS["bg"])
        win.geometry("520x520")
        win.resizable(False, False)
        win.overrideredirect(True)
        win.grab_set()

        hdr = tk.Frame(win, bg=COLORS["panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  SETTINGS", fg=COLORS["accent"], bg=COLORS["panel"],
                 font=("Consolas", 11, "bold")).pack(side="left", padx=14, pady=10)
        tk.Button(hdr, text=" ✕ ", bg=COLORS["panel"], fg=COLORS["text"],
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  activebackground=COLORS["error"], activeforeground="#fff",
                  cursor="hand2", bd=0, command=win.destroy).pack(side="right")
        tk.Frame(win, bg=COLORS["border"], height=1).pack(fill="x")

        _drag = {"x": 0, "y": 0}
        def _press(e): _drag["x"] = e.x_root - win.winfo_x(); _drag["y"] = e.y_root - win.winfo_y()
        def _move(e):  win.geometry(f"+{e.x_root - _drag['x']}+{e.y_root - _drag['y']}")
        for _w in [hdr] + [c for c in hdr.winfo_children() if isinstance(c, tk.Label)]:
            _w.bind("<ButtonPress-1>", _press)
            _w.bind("<B1-Motion>",     _move)

        body = tk.Frame(win, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=10)

        tk.Label(body, text="PRESET THEMES", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE).pack(anchor="w", pady=(0, 6))
        theme_row = tk.Frame(body, bg=COLORS["bg"])
        theme_row.pack(fill="x", pady=(0, 8))
        for tname, t in THEMES.items():
            is_cur = tname == self._current_theme
            f = tk.Frame(theme_row, bg=t["bg"],
                         highlightbackground=COLORS["accent"] if is_cur else t["border"],
                         highlightthickness=2)
            f.pack(side="left", padx=4)
            tk.Label(f, text=tname, fg=t["accent"], bg=t["bg"],
                     font=FONT_TITLE, padx=10, pady=4).pack()
            tk.Label(f, text="████", fg=t["accent"], bg=t["panel"],
                     font=("Consolas", 7), padx=4).pack(fill="x")
            for widget in [f] + list(f.winfo_children()):
                widget.bind("<Button-1>", lambda e, n=tname: self._apply_theme(n))
                widget.config(cursor="hand2")

        tk.Frame(body, bg=COLORS["border"], height=1).pack(fill="x", pady=(0, 8))

        tk.Label(body, text="CUSTOM COLOURS", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE).pack(anchor="w", pady=(0, 6))
        color_keys = [
            ("Background", "bg"),   ("Panel",    "panel"),
            ("Accent",     "accent"),("Accent 2", "accent2"),
            ("Text",       "text"),  ("Subtext",  "subtext"),
            ("Input BG",   "input_bg"),("Border", "border"),
        ]
        grid = tk.Frame(body, bg=COLORS["bg"])
        grid.pack(fill="x")
        self._color_swatches = {}
        for i, (label, key) in enumerate(color_keys):
            cell = tk.Frame(grid, bg=COLORS["bg"])
            cell.grid(row=i // 4, column=i % 4, padx=8, pady=3, sticky="w")
            tk.Label(cell, text=label, fg=COLORS["subtext"], bg=COLORS["bg"],
                     font=("Segoe UI", 7)).pack(anchor="w")
            sw = tk.Label(cell, bg=COLORS[key], width=10, height=1,
                          cursor="hand2", relief="flat")
            sw.pack(fill="x")
            sw.bind("<Button-1>", lambda e, k=key: self._pick_color_setting(k))
            self._color_swatches[key] = sw

        tk.Frame(body, bg=COLORS["border"], height=1).pack(fill="x", pady=8)

        tk.Label(body, text="STARTUP", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE).pack(anchor="w", pady=(0, 4))
        _startup_var = tk.BooleanVar(value=self._show_info_on_start)
        def _on_startup_toggle():
            self._show_info_on_start = _startup_var.get()
            self._save_settings()
        tk.Checkbutton(body, text="Show info window on startup",
                       variable=_startup_var, command=_on_startup_toggle,
                       fg=COLORS["text"], bg=COLORS["bg"],
                       selectcolor=COLORS["input_bg"],
                       activeforeground=COLORS["accent"], activebackground=COLORS["bg"],
                       font=FONT_UI).pack(anchor="w", pady=(0, 4))

        tk.Frame(body, bg=COLORS["border"], height=1).pack(fill="x", pady=8)

        btn_row = tk.Frame(body, bg=COLORS["bg"])
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="💾  SAVE AS DEFAULT", bg=COLORS["accent"], fg="#000",
                  relief="flat", font=FONT_TITLE, padx=12, pady=5,
                  cursor="hand2", command=self._save_settings).pack(side="left")
        tk.Button(btn_row, text="↺  RESET TO DARK", bg=COLORS["border"], fg=COLORS["text"],
                  relief="flat", font=FONT_TITLE, padx=12, pady=5,
                  cursor="hand2",
                  command=lambda: self._apply_theme("Dark")).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕  CLOSE", bg=COLORS["border"], fg=COLORS["warn"],
                  relief="flat", font=FONT_TITLE, padx=12, pady=5,
                  cursor="hand2", command=win.destroy).pack(side="right")

    # ─────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────
    def _build_ui(self):
        self._build_titlebar()

        # TOOLBAR
        toolbar = tk.Frame(self.root, bg=COLORS["bg"], pady=4)
        toolbar.pack(fill="x", padx=14)
        _folder_rows = [
            ("INPUT FOLDER",  self.input_folder,  getattr(self, 'pick_input', None),  None,
             "Select the folder with the images you need converted"),
            ("OUTPUT FOLDER", self.output_folder, getattr(self, 'pick_output', None), self._open_output_folder,
             "Select the folder you want the DDS files put into"),
        ]
        for lbl, var, cmd, open_cmd, hint in _folder_rows:
            row = tk.Frame(toolbar, bg=COLORS["bg"]); row.pack(fill="x", pady=2)
            tk.Label(row, text=lbl, fg=COLORS["subtext"], bg=COLORS["bg"],
                     font=FONT_TITLE, width=13, anchor="e").pack(side="left")
            ent = tk.Entry(row, bg=COLORS["input_bg"], fg=COLORS["text"],
                           insertbackground=COLORS["accent"], relief="flat",
                           font=FONT_UI, bd=4)
            ent.pack(side="left", fill="x", expand=True, padx=6)
            self._setup_placeholder(ent, var, hint)
            _br = self._btn(row, "BROWSE", cmd, COLORS["accent2"])
            _br.pack(side="left")
            self._tip(_br, f"Browse for the {lbl.lower().replace(' folder', '')} folder")
            if open_cmd:
                _op = self._btn(row, "📂 OPEN", open_cmd, COLORS["border"], fg=COLORS["text"])
                _op.pack(side="left", padx=(4, 0))
                self._tip(_op, "Open the output folder in your file explorer")

        row2 = tk.Frame(toolbar, bg=COLORS["bg"]); row2.pack(fill="x", pady=4)
        tk.Label(row2, text="OUTPUT TYPE", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE, width=13, anchor="e").pack(side="left")
        _ot_cb = ttk.Combobox(row2, textvariable=self.output_type, state="readonly", font=FONT_UI, width=8,
                              values=OUTPUT_FORMATS)
        _ot_cb.pack(side="left", padx=6)
        self._tip(_ot_cb, "Output file format. DDS = DirectX texture (requires texconv.exe). "
                          "PNG/JPG/TGA/BMP/WebP = standard images. SVG = raster embedded in SVG wrapper.")
        tk.Label(row2, text="PROFILE", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE).pack(side="left", padx=(8, 0))
        self._preset_cb = ttk.Combobox(row2, textvariable=self.preset, state="readonly",
                                       font=FONT_UI, width=28, values=PRESET_NAMES)
        self._preset_cb.pack(side="left", padx=(6, 0))
        self._tip(self._preset_cb, "Quick-apply a full preset for the target engine or use case. "
                                   "Sets DDS mode, format, and mipmap options automatically.")
        def _on_preset_change(*_):
            name = self.preset.get()
            cfg = PRESETS.get(name, {})
            # apply basic settings from preset
            if "dds_mode" in cfg:
                self.dds_mode.set(cfg["dds_mode"])
            if "format" in cfg:
                self.format.set(cfg["format"])
            if "mips" in cfg:
                self.mip_maps.set(cfg["mips"])
            # update UI states
            _on_dds_mode_change()
        self.preset.trace_add("write", _on_preset_change)
        tk.Label(row2, text="DDS FORMAT", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE).pack(side="left", padx=(8, 0))
        # DDS mode selector
        self._dds_mode_cb = ttk.Combobox(row2, textvariable=self.dds_mode, state="readonly",
                                         font=FONT_UI, width=20,
                                         values=["Legacy (Game compatible)",
                                                 "Modern (DX10/DXGI)",
                                                 "Auto (detect alpha)"])
        self._dds_mode_cb.pack(side="left", padx=(6, 0))
        self._tip(self._dds_mode_cb, "DDS header mode.\n"
                                     "Legacy = DXT1/3/5, compatible with older engines (GTA V, Skyrim).\n"
                                     "Modern = BC4/5/7 with DX10 header, for Unity/Unreal.\n"
                                     "Auto = detects alpha per-file and picks DXT1 or DXT5 automatically.")
        # DDS format combobox (values will be updated based on mode)
        self._dds_format_cb = ttk.Combobox(row2, textvariable=self.format, state="readonly",
                                           font=FONT_UI, width=16)
        self._dds_format_cb.pack(side="left", padx=6)
        self._tip(self._dds_format_cb, "Specific DDS compression codec. Overridden per-file if FILE FMT is set.\n"
                                       "DXT1=no alpha (smallest), DXT5=alpha, BC7=high quality, BC4/5=greyscale/normals.")
        # initialize formats according to mode
        def _on_dds_mode_change(*_):
            mode = self.dds_mode.get()
            # map the user-visible strings to simple checks
            if mode.startswith("Legacy"):
                vals = ["DXT1", "DXT3", "DXT5"]
                self._dds_format_cb.config(state="readonly", values=vals)
                if self.format.get() not in vals:
                    self.format.set(vals[1])
            elif mode.startswith("Modern"):
                vals = ["BC7_UNORM", "BC5_UNORM", "BC4_UNORM", "R8G8B8A8_UNORM"]
                self._dds_format_cb.config(state="readonly", values=vals)
                if self.format.get() not in vals:
                    self.format.set(vals[0])
            else:  # Auto
                # Auto chooses DXT1/DXT5 per-file; format control is disabled
                self._dds_format_cb.config(state="disabled", values=["Auto (DXT1/DXT5)"])
                self.format.set("Auto")
            if hasattr(self, "after_frame"):
                self.after_frame._title_label.config(text=f"AFTER  [ {self._get_out_ext()} ]")
        self.dds_mode.trace_add("write", _on_dds_mode_change)
        _on_dds_mode_change()
        # apply preset loaded from settings (if any)
        try:
            _on_preset_change()
        except Exception:
            pass
        self._mip_check = tk.Checkbutton(row2, text="Mipmaps", variable=self.mip_maps,
                       fg=COLORS["text"], bg=COLORS["bg"], selectcolor=COLORS["input_bg"],
                       activeforeground=COLORS["accent"], activebackground=COLORS["bg"],
                       font=FONT_UI)
        self._mip_check.pack(side="left", padx=6)
        self._tip(self._mip_check, "Generate a mipmap chain — pre-scaled versions used at lower detail levels (LOD). "
                                   "Recommended for 3D game textures. Disable for UI / 2D sprites.")

        self._quality_frame = tk.Frame(row2, bg=COLORS["bg"])
        tk.Label(self._quality_frame, text="JPG QUALITY", fg=COLORS["subtext"],
                 bg=COLORS["bg"], font=FONT_TITLE).pack(side="left", padx=(10, 4))
        self._quality_spin = tk.Spinbox(self._quality_frame, from_=1, to=100,
                                        textvariable=self.jpeg_quality,
                                        width=4, bg=COLORS["input_bg"], fg=COLORS["text"],
                                        insertbackground=COLORS["accent"],
                                        buttonbackground=COLORS["border"],
                                        relief="flat", font=FONT_UI)
        self._quality_spin.pack(side="left", padx=(0, 6))
        tk.Label(self._quality_frame,
                 text="100=lossless  95=high  85=web  75=small  60=low",
                 fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=("Segoe UI", 7, "italic")).pack(side="left")

        self.start_btn = self._btn(row2, "▶  START CONVERSION",
                                   self.start_thread, COLORS["accent"], fg="#000", padx=14)
        self.start_btn.pack(side="right")
        self._tip(self.start_btn, "Begin converting all files in the queue with the current settings")

        def _on_output_type_change(*_):
            is_dds = self.output_type.get() == "DDS"
            is_jpg = self.output_type.get() in ("JPG", "JPEG")
            # respect DDS mode: Auto disables manual format selection
            if is_dds:
                if self.dds_mode.get().startswith("Auto"):
                    self._dds_format_cb.config(state="disabled")
                else:
                    self._dds_format_cb.config(state="readonly")
            else:
                self._dds_format_cb.config(state="disabled")
            self._mip_check.config(state="normal" if is_dds else "disabled")
            if is_jpg:
                self._quality_frame.pack(side="left", after=self._mip_check)
            else:
                self._quality_frame.pack_forget()
            if hasattr(self, "after_frame"):
                self.after_frame._title_label.config(
                    text=f"AFTER  [ {self._get_out_ext()} ]")
        self.output_type.trace_add("write", _on_output_type_change)
        _on_output_type_change()

        # Performance controls
        perf_row = tk.Frame(toolbar, bg=COLORS["bg"]) ; perf_row.pack(fill="x", pady=2)
        tk.Label(perf_row, text="WORKERS", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE, width=13, anchor="e").pack(side="left")
        self._workers = tk.IntVar(value=1)
        self._workers_spin = tk.Spinbox(perf_row, from_=1, to=16, textvariable=self._workers, width=4,
                                        bg=COLORS["input_bg"], fg=COLORS["text"], relief="flat", font=FONT_UI)
        self._workers_spin.pack(side="left", padx=6)
        self._tip(self._workers_spin, "Number of parallel conversion workers (1–16). "
                                      "More workers speed up large batches on multi-core CPUs. "
                                      "Each worker runs texconv.exe as a separate subprocess.")
        self._use_gpu = tk.BooleanVar(value=False)
        _gpu_ck = tk.Checkbutton(perf_row, text="Use GPU (texconv_gpu.exe)", variable=self._use_gpu,
                       fg=COLORS["text"], bg=COLORS["bg"], selectcolor=COLORS["input_bg"],
                       activeforeground=COLORS["accent"], activebackground=COLORS["bg"], font=FONT_UI)
        _gpu_ck.pack(side="left", padx=(8,0))
        self._tip(_gpu_ck, "Use texconv_gpu.exe for GPU-accelerated block compression. "
                           "Requires the GPU-enabled build placed next to the app. Falls back to CPU if not found.")


        # Project / Template row (modding tool feel)
        proj_row = tk.Frame(toolbar, bg=COLORS["bg"]) ; proj_row.pack(fill="x", pady=2)
        tk.Label(proj_row, text="TEMPLATE", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE, width=13, anchor="e").pack(side="left")
        self._template_var = tk.StringVar(value="(none)")
        tmpl_cb = ttk.Combobox(proj_row, textvariable=self._template_var, state="readonly",
                               values=["(none)"] + list(FOLDER_TEMPLATES.keys()), width=20)
        tmpl_cb.pack(side="left", padx=6)
        self._tip(tmpl_cb, "Apply a folder template — creates input/output subfolders under the projects directory "
                           "and applies the matching preset for that asset type.")
        def _on_template_change(*_):
            val = self._template_var.get()
            if val and val != "(none)":
                self._apply_template(val)
        self._template_var.trace_add("write", _on_template_change)

        _save_proj = self._btn(proj_row, "💾 SAVE PROJECT", self._save_project, COLORS["accent"])
        _save_proj.pack(side="right", padx=4)
        self._tip(_save_proj, "Save current folders, preset, format, tints, and per-file overrides to a JSON project file")
        _load_proj = self._btn(proj_row, "📂 LOAD PROJECT", self._load_project, COLORS["border"])
        _load_proj.pack(side="right", padx=4)
        self._tip(_load_proj, "Load a previously saved project file to restore all settings, folders, and file tints")

        # Output rename rules
        rename_row = tk.Frame(toolbar, bg=COLORS["bg"]); rename_row.pack(fill="x", pady=2)
        tk.Label(rename_row, text="RENAME OUT", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE, width=13, anchor="e").pack(side="left")
        tk.Label(rename_row, text="Prefix:", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_UI).pack(side="left", padx=(6, 2))
        _pfx_ent = tk.Entry(rename_row, textvariable=self._rename_prefix,
                 bg=COLORS["input_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["accent"], relief="flat", font=FONT_UI, width=14)
        _pfx_ent.pack(side="left")
        self._tip(_pfx_ent, "Text prepended to every output filename.\nExample: 'v2_'  →  'v2_texture.dds'")
        tk.Label(rename_row, text="Suffix:", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_UI).pack(side="left", padx=(12, 2))
        _sfx_ent = tk.Entry(rename_row, textvariable=self._rename_suffix,
                 bg=COLORS["input_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["accent"], relief="flat", font=FONT_UI, width=14)
        _sfx_ent.pack(side="left")
        self._tip(_sfx_ent, "Text appended to every output filename before the extension.\nExample: '_hd'  →  'texture_hd.dds'")
        tk.Label(rename_row, text="added to each output filename before extension",
                 fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=("Segoe UI", 7, "italic")).pack(side="left", padx=8)

        tk.Frame(self.root, bg=COLORS["border"], height=1).pack(fill="x")

        # BODY
        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        # LEFT: file list
        sidebar = tk.Frame(body, bg=COLORS["sidebar"], width=230)
        sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        tk.Label(sidebar, text="FILE QUEUE", fg=COLORS["subtext"], bg=COLORS["sidebar"],
                 font=FONT_TITLE, anchor="w").pack(fill="x", padx=10, pady=(10, 2))
        self.file_count_lbl = tk.Label(sidebar, text="0 files", fg=COLORS["accent"],
                                       bg=COLORS["sidebar"], font=FONT_MONO, anchor="w")
        self.file_count_lbl.pack(fill="x", padx=10)

        # ── Bottom controls: packed side=bottom FIRST so they are always visible.
        # ── The canvas frame is packed last and fills whatever space remains.
        bot = tk.Frame(sidebar, bg=COLORS["sidebar"])
        bot.pack(side="bottom", fill="x", padx=8, pady=(0, 6))

        _reload_btn = self._btn(bot, "\u21ba  RELOAD", self.load_files, COLORS["border"], fg=COLORS["text"])
        _reload_btn.pack(fill="x")
        self._tip(_reload_btn, "Re-scan the input folder and rebuild the file queue from disk")

        tk.Frame(bot, bg=COLORS["border"], height=1).pack(fill="x", pady=(4, 3))

        qf = tk.Frame(bot, bg=COLORS["sidebar"])
        qf.pack(fill="x")
        _up_btn = self._btn(qf, "\u2191 MOVE UP", self._move_selected_up, COLORS["border"])
        _up_btn.pack(fill="x")
        self._tip(_up_btn, "Move the selected file one position up in the conversion queue")
        _dn_btn = self._btn(qf, "\u2193 MOVE DOWN", self._move_selected_down, COLORS["border"])
        _dn_btn.pack(fill="x", pady=(3, 0))
        self._tip(_dn_btn, "Move the selected file one position down in the conversion queue")
        _rm_btn = self._btn(qf, "\u2716 REMOVE", self._remove_selected, COLORS["border"], fg=COLORS["warn"])
        _rm_btn.pack(fill="x", pady=(3, 0))
        self._tip(_rm_btn, "Remove the selected file from the queue (does not delete the file from disk)")

        tk.Frame(bot, bg=COLORS["border"], height=1).pack(fill="x", pady=(4, 3))

        tk.Label(bot, text="OVERWRITE", fg=COLORS["subtext"], bg=COLORS["sidebar"],
                 font=FONT_TITLE, anchor="w").pack(fill="x")
        _ow_cb = ttk.Combobox(bot, textvariable=self.overwrite_mode, state="readonly",
                     values=["Never", "Always", "Versioned"], width=20)
        _ow_cb.pack(fill="x", pady=(2, 3))
        self._tip(_ow_cb, "How to handle output files that already exist.\n"
                          "Never = skip existing files.\n"
                          "Always = overwrite without warning.\n"
                          "Versioned = create filename_v1.dds, filename_v2.dds, etc.")

        tk.Frame(bot, bg=COLORS["border"], height=1).pack(fill="x", pady=(3, 2))

        _watch_ck = tk.Checkbutton(bot, text="Watch folder (auto-convert)",
                           variable=self.watch_mode, command=self._on_watch_toggle,
                           fg=COLORS["text"], bg=COLORS["sidebar"],
                           selectcolor=COLORS["input_bg"], activeforeground=COLORS["accent"],
                           activebackground=COLORS["sidebar"], font=FONT_UI)
        _watch_ck.pack(fill="x")
        self._tip(_watch_ck, "Poll the input folder every 1.5 s and automatically convert any new files that appear. "
                             "Useful for hot-reloading assets during development.")

        # ── Canvas / file list fills remaining space between header and bottom controls ──
        lf = tk.Frame(sidebar, bg=COLORS["sidebar"]); lf.pack(fill="both", expand=True, padx=4, pady=4)
        self._list_canvas = tk.Canvas(lf, bg="#101010", highlightthickness=0)
        self._list_canvas.pack(fill="both", expand=True)
        self._list_inner = tk.Frame(self._list_canvas, bg="#101010")
        self._list_win_id = self._list_canvas.create_window(
            (0, 0), window=self._list_inner, anchor="nw")
        self._list_inner.bind("<Configure>", lambda e: self._list_canvas.configure(
            scrollregion=self._list_canvas.bbox("all")))
        self._list_canvas.bind("<Configure>", lambda e: self._list_canvas.itemconfig(
            self._list_win_id, width=e.width))
        self._list_canvas.bind("<MouseWheel>", lambda e: self._list_canvas.yview_scroll(
            -1 * (e.delta // 120), "units"))
        self._file_names = []
        self._row_frames = {}
        self._row_labels = {}

        # CENTER
        center = tk.Frame(body, bg=COLORS["bg"])
        center.pack(side="left", fill="both", expand=True)

        ph = tk.Frame(center, bg=COLORS["bg"]); ph.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(ph, text="PREVIEW", fg=COLORS["subtext"], bg=COLORS["bg"],
                 font=FONT_TITLE).pack(side="left")
        self.preview_name_lbl = tk.Label(ph, text="", fg=COLORS["accent"],
                                         bg=COLORS["bg"], font=FONT_MONO)
        self.preview_name_lbl.pack(side="left", padx=8)
        self.tint_badge = tk.Label(ph, text="", fg="#000", bg=COLORS["panel"],
                                   font=("Consolas", 7, "bold"), padx=6, pady=1)
        self.tint_badge.pack(side="left")

        pf = tk.Frame(center, bg=COLORS["bg"])
        pf.pack(fill="both", expand=True, padx=10, pady=4)
        self.before_frame = self._preview_box(pf, "BEFORE  (with tint)")
        self.before_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.after_frame  = self._preview_box(pf, "AFTER  [ .dds ]")
        self.after_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))

        # Preview controls (zoom / checker / mip)
        ctrl_row = tk.Frame(center, bg=COLORS["bg"]) ; ctrl_row.pack(fill="x", padx=10)
        tk.Label(ctrl_row, text="Zoom:", fg=COLORS["subtext"], bg=COLORS["bg"], font=FONT_TITLE).pack(side="left")
        zoom_cb = ttk.Combobox(ctrl_row, textvariable=self._preview_zoom, state="readonly",
                               values=["Fit","25%","50%","100%","200%"], width=8)
        zoom_cb.pack(side="left", padx=(6,8))
        zoom_cb.bind("<<ComboboxSelected>>", lambda e: (self._on_preview_change()))
        self._tip(zoom_cb, "Preview zoom level. Fit = scales to fill the panel. Percentages show exact pixel size.")

        ck = tk.Checkbutton(ctrl_row, text="Checkerboard (alpha)", variable=self._preview_checker,
                            command=self._on_preview_change, fg=COLORS["text"], bg=COLORS["bg"],
                            selectcolor=COLORS["input_bg"], font=FONT_UI)
        ck.pack(side="left", padx=(0,12))
        self._tip(ck, "Show a grey checkerboard behind transparent (alpha channel) areas of the image")

        tk.Label(ctrl_row, text="MIP:", fg=COLORS["subtext"], bg=COLORS["bg"], font=FONT_TITLE).pack(side="left")
        self._mip_slider = ttk.Scale(ctrl_row, from_=0, to=0, orient="horizontal",
                                     variable=self._preview_mip_level, command=lambda v: self._on_preview_change(), length=220)
        self._mip_slider.pack(side="left", padx=(6,4))
        self._tip(self._mip_slider, "Preview mipmap level. Level 0 = full resolution. Each step halves the dimensions. "
                                    "Range is calculated from the image size.")
        self._mip_label = tk.Label(ctrl_row, text="0", fg=COLORS["subtext"], bg=COLORS["bg"], font=FONT_MONO, width=6)
        self._mip_label.pack(side="left")

        # TINT PANEL
        tint_outer = tk.Frame(center, bg=COLORS["panel"])
        tint_outer.pack(fill="x", padx=10, pady=(0, 4))

        th = tk.Frame(tint_outer, bg=COLORS["panel"]); th.pack(fill="x")
        tk.Label(th, text="⬛  TINT / SPECULAR COLOUR",
                 fg=COLORS["accent"], bg=COLORS["panel"], font=FONT_TITLE
                 ).pack(side="left", padx=10, pady=(6, 2))
        self.tint_status_lbl = tk.Label(th, text="no tint", fg=COLORS["subtext"],
                                        bg=COLORS["panel"], font=FONT_MONO)
        self.tint_status_lbl.pack(side="left", padx=8)
        tk.Label(th, text="← click an image to add a tint",
                 fg=COLORS["subtext"], bg=COLORS["panel"],
                 font=("Segoe UI", 7, "italic")).pack(side="left", padx=4)
        _ata_btn = self._btn(th, "↪  APPLY TO ALL", self._apply_to_all,
                  COLORS["border"], fg=COLORS["text"])
        _ata_btn.pack(side="right", padx=4, pady=4)
        self._tip(_ata_btn, "Apply the current colour, intensity, and blend mode to every file in the queue")
        _clr_btn = self._btn(th, "✖  CLEAR TINT", self._clear_tint,
                  COLORS["border"], fg=COLORS["warn"])
        _clr_btn.pack(side="right", padx=4, pady=4)
        self._tip(_clr_btn, "Remove the tint from the currently selected file only")

        tb = tk.Frame(tint_outer, bg=COLORS["panel"])
        tb.pack(fill="x", padx=10, pady=(2, 8))

        sw_row = tk.Frame(tb, bg=COLORS["panel"]); sw_row.pack(fill="x", pady=(0, 4))
        tk.Label(sw_row, text="PRESETS", fg=COLORS["subtext"], bg=COLORS["panel"],
                 font=FONT_TITLE, width=8, anchor="e").pack(side="left")

        for name, hx in SWATCHES:
            bg_col = hx if hx else COLORS["input_bg"]
            fg_col = "#000" if hx and luminance(hx) > 0.4 else "#fff"
            w = 3 if hx else 4
            tk.Button(sw_row, text="" if hx else name, width=w,
                      bg=bg_col, fg=fg_col, relief="flat", bd=0, cursor="hand2",
                      font=("Segoe UI", 7, "bold"), padx=3, pady=3,
                      command=lambda h=hx: self._pick_swatch(h)
                      ).pack(side="left", padx=2)

        self.custom_btn = tk.Button(
            sw_row, text="⊕ CUSTOM", bg=COLORS["input_bg"], fg=COLORS["text"],
            relief="flat", cursor="hand2", font=("Segoe UI", 7, "bold"), padx=6, pady=3,
            command=self._pick_custom)
        self.custom_btn.pack(side="left", padx=8)

        self.cur_swatch = tk.Label(sw_row, text="    ", bg=COLORS["border"],
                                   width=4, relief="flat")
        self.cur_swatch.pack(side="left", padx=4)
        self.cur_hex_lbl = tk.Label(sw_row, text="—", fg=COLORS["subtext"],
                                    bg=COLORS["panel"], font=FONT_MONO)
        self.cur_hex_lbl.pack(side="left")

        ctrl = tk.Frame(tb, bg=COLORS["panel"]); ctrl.pack(fill="x")
        tk.Label(ctrl, text="INTENSITY", fg=COLORS["subtext"], bg=COLORS["panel"],
                 font=FONT_TITLE, width=8, anchor="e").pack(side="left")
        self._pct_lbl = tk.Label(ctrl, text="40%", fg=COLORS["accent"],
                                  bg=COLORS["panel"], font=FONT_MONO, width=4)
        self._pct_lbl.pack(side="left", padx=(6, 2))
        self._slider = ttk.Scale(ctrl, from_=0, to=100, orient="horizontal",
                                  variable=self._tint_intensity,
                                  command=self._on_slider, length=200)
        self._slider.pack(side="left", padx=4)
        self._tip(self._slider, "Tint blend strength — 0% = no tint applied, 100% = fully replaced with tint colour")
        tk.Label(ctrl, text="MODE", fg=COLORS["subtext"], bg=COLORS["panel"],
                 font=FONT_TITLE, padx=10).pack(side="left")
        mode_cb = ttk.Combobox(ctrl, textvariable=self._tint_mode,
                                values=BLEND_MODES, width=14, state="readonly", font=FONT_UI)
        mode_cb.pack(side="left")
        mode_cb.bind("<<ComboboxSelected>>", lambda e: self._on_tint_changed())
        self._tip(mode_cb, "Blend mode for the tint colour.\n"
                           "Multiply = darkens/tints.  Screen = lightens.\n"
                           "Overlay = contrast boost.  Add = brightens.\n"
                           "Tint (Lerp) = straight linear blend to solid colour.")

        # Per-file DDS format override
        fmt_row = tk.Frame(tb, bg=COLORS["panel"]); fmt_row.pack(fill="x", pady=(4, 0))
        tk.Label(fmt_row, text="FILE FMT", fg=COLORS["subtext"], bg=COLORS["panel"],
                 font=FONT_TITLE, width=8, anchor="e").pack(side="left")
        self._file_fmt_var = tk.StringVar(value="(global)")
        self._file_fmt_cb = ttk.Combobox(
            fmt_row, textvariable=self._file_fmt_var, state="readonly", font=FONT_UI, width=16,
            values=["(global)", "DXT1", "DXT3", "DXT5",
                    "BC4_UNORM", "BC5_UNORM", "BC7_UNORM", "R8G8B8A8_UNORM"])
        self._file_fmt_cb.pack(side="left", padx=6)
        self._file_fmt_cb.bind("<<ComboboxSelected>>", lambda e: self._save_file_format())
        self._tip(self._file_fmt_cb, "DDS format override for this specific file only.\n"
                                     "Overrides the global format, preset, and PBR naming rules.\n"
                                     "Set back to (global) to use the global format setting.")
        tk.Label(fmt_row, text="DDS format override for this file only",
                 fg=COLORS["subtext"], bg=COLORS["panel"],
                 font=("Segoe UI", 7, "italic")).pack(side="left", padx=4)

        # Progress
        pf2 = tk.Frame(center, bg=COLORS["bg"]); pf2.pack(fill="x", padx=10, pady=(0, 4))
        self.progress_lbl = tk.Label(pf2, text="Ready", fg=COLORS["text"],
                                     bg=COLORS["bg"], font=("Consolas", 10), anchor="w")
        self.progress_lbl.pack(fill="x")
        self.progress = ttk.Progressbar(pf2, orient="horizontal",
                                        mode="determinate", style="TProgressbar")
        self.progress.pack(fill="x", pady=(2, 0))
        self.pct_bar_lbl = tk.Label(pf2, text="0%", fg=COLORS["accent"],
                                    bg=COLORS["bg"], font=("Consolas", 10, "bold"), anchor="e")
        self.pct_bar_lbl.pack(fill="x")

        # Stats
        stats_bar = tk.Frame(center, bg=COLORS["panel"], height=48)
        stats_bar.pack(fill="x", padx=10, pady=(0, 4)); stats_bar.pack_propagate(False)
        self.stat_total  = self._stat_label(stats_bar, "TOTAL",  "0")
        self.stat_done   = self._stat_label(stats_bar, "DONE",   "0", COLORS["done"])
        self.stat_fail   = self._stat_label(stats_bar, "FAIL",   "0", COLORS["fail"])
        self.stat_tinted = self._stat_label(stats_bar, "TINTED", "0", COLORS["warn"])

        # RIGHT: log
        log_outer = tk.Frame(body, bg=COLORS["sidebar"], width=310)
        log_outer.pack(side="right", fill="y"); log_outer.pack_propagate(False)
        lh = tk.Frame(log_outer, bg=COLORS["sidebar"]); lh.pack(fill="x")
        tk.Label(lh, text="CONVERSION LOG", fg=COLORS["subtext"],
                 bg=COLORS["sidebar"], font=FONT_TITLE).pack(side="left", padx=10, pady=(8, 4))
        _clr_log = self._btn(lh, "CLEAR", self.clear_log, COLORS["border"], fg=COLORS["text"])
        _clr_log.pack(side="right", padx=8, pady=4)
        self._tip(_clr_log, "Clear the conversion log panel (does not affect texforge_conversion.log on disk)")
        log_sb2 = tk.Scrollbar(log_outer); log_sb2.pack(side="right", fill="y")
        self.log = tk.Text(log_outer, bg="#0a0a0a", fg=COLORS["text"], font=FONT_MONO,
                           relief="flat", bd=0, wrap="none", state="disabled", cursor="arrow")
        self.log.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.log.config(yscrollcommand=log_sb2.set)
        log_sb2.config(command=self.log.yview)
        for tag, fg, bold in [
            ("time",   COLORS["subtext"], False),
            ("info",   COLORS["info"],    False),
            ("done",   COLORS["done"],    False),
            ("fail",   COLORS["fail"],    False),
            ("warn",   COLORS["warn"],    False),
            ("sub",    COLORS["subtext"], False),
            ("normal", COLORS["text"],    False),
            ("head",   COLORS["accent"],  True),
            ("tint",   COLORS["warn"],    True),
        ]:
            kw = {"foreground": fg}
            if bold: kw["font"] = ("Consolas", 9, "bold")
            self.log.tag_config(tag, **kw)

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────
    def _btn(self, parent, text, cmd, bg, fg="white", padx=8):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         relief="flat", font=FONT_TITLE, padx=padx, pady=3,
                         activebackground=COLORS["border"], activeforeground=fg, cursor="hand2")

    def _tip(self, widget, text: str):
        """Attach a hover tooltip to widget and return it."""
        _Tooltip(widget, text)
        return widget

    def _preview_box(self, parent, label):
        frame = tk.Frame(parent, bg=COLORS["panel"])
        title_lbl = tk.Label(frame, text=label, fg=COLORS["subtext"], bg=COLORS["panel"],
                             font=FONT_TITLE)
        title_lbl.pack(pady=(6, 2))
        frame._title_label = title_lbl
        lbl = tk.Label(frame, bg="#0d0d0d"); lbl.pack(fill="both", expand=True, padx=6, pady=(0, 2))
        frame._img_label  = lbl
        frame._info_label = tk.Label(frame, text="", fg=COLORS["subtext"],
                                     bg=COLORS["panel"], font=FONT_MONO)
        frame._info_label.pack(pady=(0, 4))
        return frame

    def _stat_label(self, parent, title, value, color=None):
        color = color or COLORS["text"]
        f = tk.Frame(parent, bg=COLORS["panel"]); f.pack(side="left", padx=12, pady=4)
        vl = tk.Label(f, text=value, fg=color, bg=COLORS["panel"], font=FONT_STAT); vl.pack()
        tk.Label(f, text=title, fg=COLORS["subtext"], bg=COLORS["panel"],
                 font=("Segoe UI", 9)).pack()
        return vl

    def _setup_placeholder(self, entry, var, placeholder):
        _guard = [False]

        def _show():
            entry.delete(0, tk.END)
            entry.insert(0, placeholder)
            entry.config(fg=COLORS["subtext"])

        def _is_placeholder():
            return entry.get() == placeholder and entry.cget("fg") == COLORS["subtext"]

        def on_focus_in(e):
            if _is_placeholder():
                entry.delete(0, tk.END)
                entry.config(fg=COLORS["text"])

        def on_focus_out(e):
            if not entry.get().strip():
                _show()
                if not _guard[0]:
                    _guard[0] = True
                    var.set("")
                    _guard[0] = False

        def on_key(e):
            if not _guard[0]:
                _guard[0] = True
                var.set(entry.get())
                _guard[0] = False

        def on_var_change(*_):
            if _guard[0]:
                return
            val = var.get()
            _guard[0] = True
            if val:
                entry.delete(0, tk.END)
                entry.insert(0, val)
                entry.config(fg=COLORS["text"])
            else:
                _show()
            _guard[0] = False

        if var.get():
            entry.insert(0, var.get())
            entry.config(fg=COLORS["text"])
        else:
            _show()

        entry.bind("<FocusIn>",    on_focus_in)
        entry.bind("<FocusOut>",   on_focus_out)
        entry.bind("<KeyRelease>", on_key)
        var.trace_add("write", on_var_change)

    # ─────────────────────────────────────────
    # PROJECTS / TEMPLATES
    # ─────────────────────────────────────────
    def _ensure_projects_dir(self):
        try:
            os.makedirs(PROJECTS_DIR, exist_ok=True)
        except Exception:
            pass

    def _save_project(self):
        self._ensure_projects_dir()
        # ask for filename
        p = filedialog.asksaveasfilename(title="Save project", initialdir=PROJECTS_DIR,
                                         defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not p:
            return
        data = {
            "input_folder": self.input_folder.get(),
            "output_folder": self.output_folder.get(),
            "preset": self.preset.get(),
            "output_type": self.output_type.get(),
            "format": self.format.get(),
            "dds_mode": self.dds_mode.get(),
            "mips": bool(self.mip_maps.get()),
            "overwrite_mode": self.overwrite_mode.get(),
            "watch_mode": bool(self.watch_mode.get()),
            "jpeg_quality": int(self.jpeg_quality.get()),
            "file_tints": self._file_tints,
            "file_formats": self._file_formats,
            "rename_prefix": self._rename_prefix.get(),
            "rename_suffix": self._rename_suffix.get(),
        }
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._log("info", f"Project saved: {os.path.basename(p)}")
        except Exception as e:
            self._log("warn", f"Could not save project: {e}")

    def _load_project(self):
        self._ensure_projects_dir()
        p = filedialog.askopenfilename(title="Load project", initialdir=PROJECTS_DIR,
                                       filetypes=[("JSON files","*.json")])
        if not p:
            return
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self._log("warn", f"Could not load project: {e}")
            return
        # apply settings
        try:
            if data.get("input_folder"):
                self.input_folder.set(data.get("input_folder"))
            if data.get("output_folder"):
                self.output_folder.set(data.get("output_folder"))
            if data.get("preset"):
                self.preset.set(data.get("preset"))
            if data.get("output_type"):
                self.output_type.set(data.get("output_type"))
            if data.get("format"):
                self.format.set(data.get("format"))
            if data.get("dds_mode"):
                self.dds_mode.set(data.get("dds_mode"))
            if "mips" in data:
                self.mip_maps.set(bool(data.get("mips")))
            if data.get("overwrite_mode"):
                self.overwrite_mode.set(data.get("overwrite_mode"))
            if "watch_mode" in data:
                self.watch_mode.set(bool(data.get("watch_mode")))
            if "jpeg_quality" in data:
                self.jpeg_quality.set(int(data.get("jpeg_quality")))
            if "file_tints" in data:
                self._file_tints = data.get("file_tints") or {}
            if "file_formats" in data:
                self._file_formats = data.get("file_formats") or {}
            if "rename_prefix" in data:
                self._rename_prefix.set(data.get("rename_prefix", ""))
            if "rename_suffix" in data:
                self._rename_suffix.set(data.get("rename_suffix", ""))
            # refresh UI
            self._save_settings(silent=True)
            self.load_files()
            self._log("info", f"Project loaded: {os.path.basename(p)}")
        except Exception as e:
            self._log("warn", f"Could not apply project settings: {e}")

    def _apply_template(self, name: str):
        t = FOLDER_TEMPLATES.get(name)
        if not t:
            return
        inp = os.path.join(APP_DIR, "projects", t["input_sub"])
        out = os.path.join(APP_DIR, "projects", t["output_sub"])
        try:
            os.makedirs(inp, exist_ok=True)
            os.makedirs(out, exist_ok=True)
            self.input_folder.set(inp)
            self.output_folder.set(out)
            preset = t.get("preset")
            if preset:
                # only set if present in PRESETS
                if preset in PRESETS:
                    self.preset.set(preset)
            self._save_settings(silent=True)
            self.load_files()
            self._log("info", f"Applied template: {name}")
        except Exception as e:
            self._log("warn", f"Template apply failed: {e}")

    def _add_file_row(self, fname):
        row = tk.Frame(self._list_inner, bg="#101010", cursor="hand2")
        row.pack(fill="x", pady=1, padx=2)
        btn = tk.Button(row, text="▶", bg=COLORS["border"], fg=COLORS["accent"],
                        relief="flat", font=("Consolas", 7, "bold"), padx=4, pady=1,
                        cursor="hand2",
                        command=lambda f=fname: self._convert_single(f))
        btn.pack(side="right", padx=(0, 3), pady=2)
        lbl = tk.Label(row, text=fname, bg="#101010", fg=COLORS["text"],
                       font=FONT_MONO, anchor="w", padx=4, pady=3)
        lbl.pack(side="left", fill="x", expand=True)
        for w in [row, lbl]:
            w.bind("<Button-1>", lambda e, f=fname: self._select_file_row(f))
        for w in [row, lbl, btn]:
            w.bind("<MouseWheel>", lambda e: self._list_canvas.yview_scroll(
                -1 * (e.delta // 120), "units"))
        self._row_frames[fname] = row
        self._row_labels[fname] = lbl

    def _select_file_row(self, fname):
        for f, frm in self._row_frames.items():
            frm.config(bg="#101010")
            self._row_labels[f].config(bg="#101010")
        if fname in self._row_frames:
            self._row_frames[fname].config(bg=COLORS["accent2"])
            self._row_labels[fname].config(bg=COLORS["accent2"], fg="#fff")
        self._refresh_list_colors()
        self._on_file_select(fname)

    # ─────────────────────────────────────────
    # FOLDERS
    # ─────────────────────────────────────────
    def pick_input(self):
        f = filedialog.askdirectory()
        if f: self.input_folder.set(f); self.load_files(); self._save_settings(silent=True)

    def pick_output(self):
        f = filedialog.askdirectory()
        if f: self.output_folder.set(f); self._save_settings(silent=True)

    def _open_output_folder(self):
        path = self.output_folder.get()
        if path and os.path.isdir(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        else:
            messagebox.showinfo("No folder", "Set an output folder first.")

    # ─────────────────────────────────────────
    # FILE LIST
    # ─────────────────────────────────────────
    def load_files(self):
        for w in self._list_inner.winfo_children():
            w.destroy()
        self._row_frames.clear()
        self._row_labels.clear()
        self._file_names = []
        folder = self.input_folder.get()
        if not folder or not os.path.isdir(folder):
            self.file_count_lbl.config(text="0 file(s)")
            self.stat_total.config(text="0")
            return
        files = sorted(f for f in os.listdir(folder) if f.lower().endswith(VALID_EXTENSIONS))
        self._file_names = files
        for f in files:
            self._add_file_row(f)
        self.file_count_lbl.config(text=f"{len(files)} file(s)")
        self.stat_total.config(text=str(len(files)))
        self._log("info", f"Loaded {len(files)} file(s)")
        self._refresh_list_colors()

    # ─────────────────────────────────────────
    # FILE SELECT
    # ─────────────────────────────────────────
    def _get_out_ext(self):
        ot = self.output_type.get()
        if ot == "DDS":  return ".dds"
        if ot == "SVG":  return ".svg"
        if ot in ("JPG", "JPEG"): return ".jpg"
        return f".{ot.lower()}"

    def _on_file_select(self, fname):
        if not fname or not self.input_folder.get(): return
        self._selected_file = fname
        self.preview_name_lbl.config(text=fname)
        tint = self._file_tints.get(fname, {})
        self._tint_color.set(tint.get("color", ""))
        self._tint_intensity.set(tint.get("intensity", 0.40) * 100)
        self._tint_mode.set(tint.get("mode", "Multiply"))
        self._sync_tint_ui()
        if hasattr(self, "_file_fmt_var"):
            self._file_fmt_var.set(self._file_formats.get(fname, "(global)"))
        self._refresh_before_preview()
        if self.output_folder.get():
            stem     = os.path.splitext(fname)[0]
            out_file = os.path.join(self.output_folder.get(), stem + self._get_out_ext())
            if os.path.exists(out_file):
                self._show_path(out_file, self.after_frame)
            else:
                self._clear_preview(self.after_frame, "not converted yet")

    # ─────────────────────────────────────────
    # TINT CONTROLS
    # ─────────────────────────────────────────
    def _pick_swatch(self, hx):
        if hx is None:
            self._clear_tint(); return
        self._tint_color.set(hx)
        self._on_tint_changed()

    def _pick_custom(self):
        init = self._tint_color.get() or "#FFFFFF"
        result = colorchooser.askcolor(color=init, title="Pick tint colour")
        if result and result[1]:
            self._tint_color.set(result[1].upper())
            self._on_tint_changed()

    def _on_slider(self, val=None):
        pct = int(float(val if val is not None else self._tint_intensity.get()))
        self._pct_lbl.config(text=f"{pct}%")
        self._save_tint()
        self._refresh_before_preview()

    def _on_tint_changed(self):
        self._sync_tint_ui()
        self._save_tint()
        self._refresh_before_preview()

    def _sync_tint_ui(self):
        hx  = self._tint_color.get()
        pct = int(self._tint_intensity.get())
        self._pct_lbl.config(text=f"{pct}%")
        if hx:
            lum = luminance(hx)
            self.cur_swatch.config(bg=hx)
            self.cur_hex_lbl.config(text=hx, fg=hx if lum > 0.15 else COLORS["text"])
            self.tint_status_lbl.config(
                text=f"{hx}  {pct}%  [{self._tint_mode.get()}]", fg=COLORS["warn"])
            self.tint_badge.config(
                text=f"  TINT {hx} {pct}%  ",
                bg=hx, fg="#000" if lum > 0.4 else "#fff")
        else:
            self.cur_swatch.config(bg=COLORS["border"])
            self.cur_hex_lbl.config(text="—", fg=COLORS["subtext"])
            self.tint_status_lbl.config(text="no tint", fg=COLORS["subtext"])
            self.tint_badge.config(text="", bg=COLORS["panel"])

    def _save_tint(self):
        if not self._selected_file: return
        hx  = self._tint_color.get()
        pct = self._tint_intensity.get()
        if hx:
            self._file_tints[self._selected_file] = {
                "color":     hx,
                "intensity": pct / 100.0,
                "mode":      self._tint_mode.get(),
            }
        else:
            self._file_tints.pop(self._selected_file, None)
        self._refresh_list_colors()
        self.stat_tinted.config(text=str(len(self._file_tints)))

    def _save_file_format(self):
        if not self._selected_file: return
        fmt = self._file_fmt_var.get()
        if fmt and fmt != "(global)":
            self._file_formats[self._selected_file] = fmt
        else:
            self._file_formats.pop(self._selected_file, None)

    def _clear_tint(self):
        self._tint_color.set("")
        self._sync_tint_ui()
        self._save_tint()
        self._refresh_before_preview()

    def _apply_to_all(self):
        hx  = self._tint_color.get()
        pct = self._tint_intensity.get()
        if not hx:
            messagebox.showinfo("No colour", "Choose a tint colour first."); return
        n = len(self._file_names)
        for fname in self._file_names:
            self._file_tints[fname] = {
                "color":     hx,
                "intensity": pct / 100.0,
                "mode":      self._tint_mode.get(),
            }
        self._refresh_list_colors()
        self.stat_tinted.config(text=str(len(self._file_tints)))
        self._log("tint", f"Applied {hx} @ {int(pct)}% [{self._tint_mode.get()}] → {n} files")

    def _refresh_list_colors(self):
        for fname in self._file_names:
            if fname not in self._row_labels:
                continue
            if fname == self._selected_file:
                continue
            if fname in self._file_tints:
                c = self._file_tints[fname]["color"]
                r, g, b = hex_to_rgb(c)
                r = min(255, r + 60); g = min(255, g + 60); b = min(255, b + 60)
                self._row_labels[fname].config(fg=f"#{r:02X}{g:02X}{b:02X}")
            else:
                self._row_labels[fname].config(fg=COLORS["text"])

    # ─────────────────────────────────────────
    # PREVIEW
    # ─────────────────────────────────────────
    def _refresh_before_preview(self):
        if not self._selected_file or not self.input_folder.get(): return
        src = os.path.join(self.input_folder.get(), self._selected_file)
        try:
            img = Image.open(src)
            hx  = self._tint_color.get()
            if hx:
                img = apply_tint(img, hx, self._tint_intensity.get() / 100.0,
                                 self._tint_mode.get())
            self._preview_src_img = img.copy()
            # update mip slider range
            self._update_mip_slider(self._preview_src_img)
            self._render_preview(self._preview_src_img, self.before_frame, os.path.getsize(src))
        except Exception as e:
            self.before_frame._img_label.config(image="", text=f"⚠ {e}",
                                                fg=COLORS["warn"], compound="center")

    def _show_path(self, path, box):
        if path.lower().endswith(".svg"):
            sz = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
            box._img_label.config(image="", text="SVG\n(raster embedded)\nno preview",
                                  fg=COLORS["subtext"], compound="center")
            box._img_label._photo = None
            box._info_label.config(text=f"{sz:.1f} KB  •  SVG")
            return
        try:
            img = Image.open(path)
            if box is self.after_frame:
                self._preview_after_img = img.copy()
                self._update_mip_slider(self._preview_after_img)
                self._render_preview(self._preview_after_img, box, os.path.getsize(path))
            else:
                self._render_preview(img, box, os.path.getsize(path))
        except Exception as e:
            box._img_label.config(image="", text=f"⚠ {e}",
                                  fg=COLORS["warn"], compound="center")

    def _display(self, img: Image.Image, box, size_bytes=0):
        # legacy simple display — kept for compatibility
        w, h = img.size
        th = img.copy(); th.thumbnail((320, 260))
        photo = ImageTk.PhotoImage(th)
        box._img_label.config(image=photo, text="")
        box._img_label._photo = photo
        box._info_label.config(text=f"{w}×{h}px  •  {size_bytes/1024:.1f} KB  •  {img.mode}")

    def _clear_preview(self, box, reason=""):
        box._img_label.config(image="", text=reason, fg=COLORS["subtext"], compound="center")
        box._img_label._photo = None
        box._info_label.config(text="")
        # clear cached images if clearing both
        if box is self.before_frame:
            self._preview_src_img = None
        if box is self.after_frame:
            self._preview_after_img = None

    def _try_refresh_after(self, fname):
        if self._selected_file == fname and self.output_folder.get():
            out_file = os.path.join(self.output_folder.get(),
                                    os.path.splitext(fname)[0] + self._get_out_ext())  # no-op change
            if os.path.exists(out_file):
                self._show_path(out_file, self.after_frame)

    # ─────────────────────────────────────────
    # LOG
    # ─────────────────────────────────────────
    def _log(self, kind, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert(tk.END, f"[{ts}] ", "time")
        self.log.insert(tk.END, msg + "\n", kind)
        self.log.config(state="disabled")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.config(state="disabled")

    # ─────────────────────────────────────────
    # PROGRESS
    # ─────────────────────────────────────────
    def _set_progress(self, i, total, label=""):
        self.progress["maximum"] = total
        self.progress["value"]   = i
        pct = int(i / total * 100) if total else 0
        self.pct_bar_lbl.config(text=f"{pct}%")
        if label: self.progress_lbl.config(text=label)
        self.root.update_idletasks()

    # ─────────────────────────────────────────
    # THREAD / CONVERT
    # ─────────────────────────────────────────
    def start_thread(self):
        if self._converting: return
        self._converting = True
        self.start_btn.config(state="disabled", text="⏳  CONVERTING…")
        threading.Thread(target=self._convert_wrapper, daemon=True).start()

    def _convert_wrapper(self, files=None):
        try:
            self._do_convert(files=files)
        finally:
            self._converting = False
            # if watch added pending files while converting, start them now
            if self._pending_watch_files:
                pending = self._pending_watch_files.copy()
                self._pending_watch_files.clear()
                threading.Thread(target=lambda: self._convert_wrapper(files=pending), daemon=True).start()
            else:
                self.root.after(0, lambda: self.start_btn.config(
                    state="normal", text="▶  START CONVERSION"))

    def _convert_single(self, fname):
        if self._converting: return
        self._converting = True
        self.start_btn.config(state="disabled", text="⏳  CONVERTING…")
        threading.Thread(
            target=lambda: self._convert_wrapper(files=[fname]), daemon=True).start()

    def start_thread_for_files(self, files):
        """Start conversion for specific files (used by watch mode)."""
        if not files:
            return
        if self._converting:
            # queue them
            self._pending_watch_files.extend(files)
            self._log("info", f"Watch: queued {len(files)} new file(s)")
            return
        self._converting = True
        self.start_btn.config(state="disabled", text="⏳  CONVERTING…")
        threading.Thread(target=lambda: self._convert_wrapper(files=files), daemon=True).start()

    def _do_convert(self, files=None):
        texconv  = os.path.join(APP_DIR, TEXCONV_PATH)
        inp      = self.input_folder.get()
        out      = self.output_folder.get()
        fmt_default = self.format.get()
        mips     = self.mip_maps.get()
        out_type = self.output_type.get()
        is_dds   = out_type == "DDS"
        out_ext  = self._get_out_ext()

        errs = []
        if is_dds and not os.path.exists(texconv):
            errs.append(f"texconv.exe not found: {texconv}")
        if not inp or not os.path.isdir(inp): errs.append("Input folder invalid or not set")
        if not out: errs.append("Output folder not set")
        if errs:
            for e in errs: self._log("fail", f"ERROR: {e}")
            messagebox.showerror("Error", "\n".join(errs)); return

        inp = os.path.abspath(inp)
        out = os.path.abspath(out)
        os.makedirs(out, exist_ok=True)

        if files is None:
            files = sorted(f for f in os.listdir(inp) if f.lower().endswith(VALID_EXTENSIONS))
        total = len(files)
        if total == 0:
            self._log("warn", "No valid image files found"); return

        done_n = fail_n = 0
        self.stat_done.config(text="0"); self.stat_fail.config(text="0")
        self._set_progress(0, total, "Starting…")

        self._log("head", "═" * 36)
        if is_dds:
            mode_lbl = self.dds_mode.get()
            if mode_lbl.startswith("Auto"):
                label = "DDS / Auto (DXT1/DXT5)"
            else:
                label = f"DDS / {mode_lbl.split()[0]} / {fmt_default}"
        else:
            label = out_type
        self._log("head", f" START  {total} file(s)  →  {label}")
        self._log("head", f" Tinted: {len(self._file_tints)} file(s)")
        self._log("head", "═" * 36)

        t0      = datetime.now()
        manifest_entries = []
        tmp_out = []
        # Prepare concurrency
        import concurrent.futures
        write_lock = threading.Lock()
        workers = max(1, int(self._workers.get()))

        texconv_bin = os.path.join(APP_DIR, TEXCONV_PATH)
        if self._use_gpu.get():
            gpu_path = os.path.join(APP_DIR, "texconv_gpu.exe")
            if os.path.exists(gpu_path):
                texconv_bin = gpu_path
            else:
                self._log("warn", "GPU texconv requested but texconv_gpu.exe not found; falling back to CPU texconv.")

        def convert_file(fname, idx):
            """Convert a single file. Returns a result dict."""
            src = os.path.join(inp, fname)
            stem = os.path.splitext(fname)[0]
            extn = os.path.splitext(fname)[1]
            convert_src = src
            tmp_path = None
            result_rec = {"fname": fname, "index": idx, "success": False, "skipped": False, "dst": None, "format": "", "reason": ""}

            # Tint bake
            tint = self._file_tints.get(fname)
            if tint:
                try:
                    img = Image.open(src)
                    baked = apply_tint(img, tint["color"], tint["intensity"], tint["mode"])
                    tmp = tempfile.NamedTemporaryFile(suffix=extn, delete=False)
                    tmp_path = tmp.name; tmp.close()
                    baked.save(tmp_path)
                    convert_src = tmp_path
                except Exception as e:
                    # fallback to original
                    convert_src = src

            _pfx = self._rename_prefix.get().strip()
            _sfx = self._rename_suffix.get().strip()
            out_stem = f"{_pfx}{stem}{_sfx}" if (_pfx or _sfx) else stem
            dst_file = os.path.join(out, out_stem + out_ext)

            # Overwrite/version rules guarded by lock
            with write_lock:
                if os.path.exists(dst_file):
                    if self.overwrite_mode.get() == "Never":
                        result_rec.update({"success": True, "skipped": True, "dst": dst_file, "format": "" , "reason": "already exists"})
                        # cleanup tmp
                        if tmp_path:
                            try: os.unlink(tmp_path)
                            except: pass
                        return result_rec
                    elif self.overwrite_mode.get() == "Versioned":
                        base, extn2 = os.path.splitext(dst_file)
                        n = 1
                        while os.path.exists(f"{base}_v{n}{extn2}"):
                            n += 1
                        dst_file = f"{base}_v{n}{extn2}"

            # do conversion
            try:
                if is_dds:
                    mode = self.dds_mode.get()
                    # detect alpha
                    try:
                        probe = Image.open(convert_src)
                        bands = probe.getbands()
                        if "A" in bands:
                            a = probe.getchannel("A")
                            lo, hi = a.getextrema()
                            has_alpha = lo < 255
                        else:
                            has_alpha = False
                    except Exception:
                        has_alpha = True
                    file_fmt = "DXT5" if has_alpha else "DXT1" if mode.startswith("Auto") else fmt_default

                    # preset overrides
                    p = PRESETS.get(self.preset.get(), {})
                    lower = stem.lower()
                    if p.get("pbr_rules"):
                        if any(k in lower for k in ("normal", "nrm", "nrml")):
                            file_fmt = "BC5_UNORM"
                        elif any(k in lower for k in ("rough", "roughness", "rgh")):
                            file_fmt = "BC4_UNORM"
                        elif any(k in lower for k in ("metal", "metallic", "metalness")):
                            file_fmt = "BC4_UNORM"
                        elif any(k in lower for k in ("albedo", "basecolor", "diffuse", "diff")):
                            file_fmt = "BC7_UNORM"

                    # per-file format override takes priority over everything else
                    _per_fmt = self._file_formats.get(fname)
                    if _per_fmt and _per_fmt != "(global)":
                        file_fmt = _per_fmt

                    cmd = [texconv_bin, "-f", file_fmt, "-o", out, "-y"]
                    if not mips: cmd += ["-m", "1"]
                    cmd.append(convert_src)
                    proc = subprocess.run(cmd, capture_output=True, text=True)

                    # handle tmp->dst rename
                    if tmp_path:
                        tmp_stem = os.path.splitext(os.path.basename(tmp_path))[0]
                        src_dds = os.path.join(out, tmp_stem + ".dds")
                        if os.path.exists(src_dds) and src_dds != dst_file:
                            try:
                                os.replace(src_dds, dst_file)
                            except Exception:
                                try:
                                    import shutil
                                    shutil.copyfile(src_dds, dst_file)
                                except Exception:
                                    pass

                    for line in proc.stdout.strip().splitlines():
                        # log lines will be processed by main _do_convert thread
                        pass
                    for line in proc.stderr.strip().splitlines():
                        pass

                    success = proc.returncode == 0
                    result_rec.update({"success": success, "dst": dst_file, "format": file_fmt})
                    if not success:
                        result_rec["reason"] = proc.stderr.strip() or f"exit {proc.returncode}"
                elif out_type == "SVG":
                    try:
                        img = Image.open(convert_src)
                        save_as_svg(img, dst_file)
                        result_rec.update({"success": True, "dst": dst_file, "format": "SVG"})
                    except Exception as e:
                        result_rec.update({"success": False, "dst": dst_file, "format": "SVG", "reason": str(e)})
                else:
                    try:
                        img = Image.open(convert_src)
                        pil_fmt = "JPEG" if out_type in ("JPG","JPEG") else out_type
                        if pil_fmt == "JPEG" and img.mode in ("RGBA","LA","P"):
                            img = img.convert("RGB")
                        save_kwargs = {}
                        if pil_fmt == "JPEG":
                            save_kwargs["quality"] = self.jpeg_quality.get()
                            save_kwargs["optimize"] = True
                        img.save(dst_file, format=pil_fmt, **save_kwargs)
                        result_rec.update({"success": True, "dst": dst_file, "format": out_type})
                    except Exception as e:
                        result_rec.update({"success": False, "dst": dst_file, "format": out_type, "reason": str(e)})
            finally:
                if tmp_path:
                    try: os.unlink(tmp_path)
                    except: pass

            return result_rec

        # ── Shared result handler (used by both sequential and parallel paths) ──
        def _handle_result(res, i):
            nonlocal done_n, fail_n
            file_fmt = res.get("format", "")
            dst_file = res.get("dst")
            fname_r  = res.get("fname", "")

            # ETA estimation
            _elapsed = (datetime.now() - t0).total_seconds()
            _rate    = _elapsed / i if i > 0 else 0
            _eta     = f"  ETA ~{int(_rate * (total - i))}s" if i < total and _rate > 0 else ""
            _prog_label = f"[{i}/{total}]  {fname_r}{_eta}"

            if res.get("skipped"):
                self._log_file_status("SKIP", os.path.basename(dst_file),
                                      reason=res.get("reason", "already exists"))
                try:
                    size_b = os.path.getsize(dst_file) if os.path.exists(dst_file) else 0
                    manifest_entries.append({"file": os.path.basename(dst_file), "status": "SKIP",
                                             "format": "", "reason": res.get("reason", ""), "size": size_b})
                except Exception:
                    pass
                done_n += 1
                self.stat_done.config(text=str(done_n))
                self.root.after(0, lambda f=fname_r: self._try_refresh_after(f))
                self.root.after(0, lambda _i=i-1: self._mark_row(_i, True))
                self._set_progress(i, total, _prog_label)
                return

            if res.get("success"):
                sz = f"  ({os.path.getsize(dst_file)/1024:.1f} KB)" if os.path.exists(dst_file) else ""
                self._log("done", f"  ✔ {os.path.splitext(fname_r)[0]}{out_ext}{sz}")
                note = ""
                if is_dds and self.dds_mode.get().startswith("Auto"):
                    note = "alpha detected" if file_fmt.startswith("DXT5") else "no alpha"
                self._log_file_status("OK", os.path.basename(dst_file), reason=note, fmt=file_fmt)
                done_n += 1
                self.stat_done.config(text=str(done_n))
                self.root.after(0, lambda f=fname_r: self._try_refresh_after(f))
            else:
                self._log("fail", f"  ✘ FAILED: {fname_r}  ({res.get('reason', '')})")
                self._log_file_status("FAIL", fname_r, reason=res.get("reason", ""), fmt=file_fmt)
                fail_n += 1
                self.stat_fail.config(text=str(fail_n))

            try:
                out_name = os.path.basename(dst_file) if dst_file else os.path.basename(fname_r)
                size_b   = os.path.getsize(dst_file) if dst_file and os.path.exists(dst_file) else 0
                manifest_entries.append({"file": out_name,
                                         "status": "OK" if res.get("success") else "FAIL",
                                         "format": file_fmt, "reason": res.get("reason", ""),
                                         "size": size_b})
            except Exception:
                pass

            self.root.after(0, lambda _i=i-1, _ok=res.get("success"): self._mark_row(_i, _ok))
            self._set_progress(i, total, _prog_label)

        # ── Dispatch: sequential or parallel with chunking ──
        chunk_size = max(1, min(256, workers * 8))
        if workers <= 1:
            for i, fname in enumerate(files, 1):
                self._set_progress(i - 1, total, f"[{i}/{total}]  {fname}")
                self._log("sub", f"──── [{i}/{total}] {fname}")
                _handle_result(convert_file(fname, i - 1), i)
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            for chunk_start in range(0, len(files), chunk_size):
                chunk = files[chunk_start:chunk_start + chunk_size]
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futures = {ex.submit(convert_file, fname, chunk_start + off): fname
                               for off, fname in enumerate(chunk)}
                    for fut in as_completed(futures):
                        res = fut.result()
                        _handle_result(res, res.get("index", 0) + 1)

        for p in tmp_out:
            try: os.unlink(p)
            except: pass

        # write export manifest into output folder (single rolling file, overwritten each run)
        try:
            if manifest_entries and out:
                manifest_path = os.path.join(out, "export_manifest.json")
                with open(manifest_path, "w", encoding="utf-8") as mf:
                    json.dump({"generated": datetime.now().isoformat(),
                               "total": total, "done": done_n, "failed": fail_n,
                               "entries": manifest_entries}, mf, indent=2, ensure_ascii=False)
                self._log("info", f"Manifest: {manifest_path}")
        except Exception as e:
            self._log("warn", f"Manifest write failed: {e}")

        elapsed = (datetime.now() - t0).seconds
        self._log("head", "═" * 36)
        self._log("done" if fail_n == 0 else "warn",
                  f" ✔ {done_n}  ✘ {fail_n}  in {elapsed}s")
        self._log("head", "═" * 36)
        self._set_progress(total, total, "Done")
        self.progress_lbl.config(text=f"✔ {done_n}/{total} converted in {elapsed}s")

    def _mark_row(self, idx, success):
        try:
            if idx < len(self._file_names):
                fname = self._file_names[idx]
                if fname != self._selected_file and fname in self._row_labels:
                    self._row_labels[fname].config(
                        fg=COLORS["done"] if success else COLORS["fail"])
        except Exception:
            pass

    # ─────────────────────────────────────────
    # QUEUE / WATCH HELPERS
    # ─────────────────────────────────────────
    def _move_selected_up(self):
        f = self._selected_file
        if not f or f not in self._file_names: return
        idx = self._file_names.index(f)
        if idx > 0:
            self._file_names[idx], self._file_names[idx-1] = self._file_names[idx-1], self._file_names[idx]
            self._rebuild_file_list_order()

    def _move_selected_down(self):
        f = self._selected_file
        if not f or f not in self._file_names: return
        idx = self._file_names.index(f)
        if idx < len(self._file_names) - 1:
            self._file_names[idx], self._file_names[idx+1] = self._file_names[idx+1], self._file_names[idx]
            self._rebuild_file_list_order()

    def _rebuild_file_list_order(self):
        """Re-pack existing row widgets in the current _file_names order without re-reading disk."""
        for fname in self._file_names:
            if fname in self._row_frames:
                self._row_frames[fname].pack_forget()
        for fname in self._file_names:
            if fname in self._row_frames:
                self._row_frames[fname].pack(fill="x", pady=1, padx=2)
        self._refresh_list_colors()
        if self._selected_file and self._selected_file in self._row_frames:
            self._row_frames[self._selected_file].config(bg=COLORS["accent2"])
            self._row_labels[self._selected_file].config(bg=COLORS["accent2"], fg="#fff")

    def _remove_selected(self):
        f = self._selected_file
        if not f: return
        if f in self._file_names:
            self._file_names.remove(f)
        if f in self._row_frames:
            try:
                self._row_frames[f].destroy()
            except Exception:
                pass
        self._selected_file = None
        self._refresh_list_colors()

    def _on_watch_toggle(self):
        if self.watch_mode.get():
            # start watching
            fld = self.input_folder.get()
            if not fld or not os.path.isdir(fld):
                messagebox.showinfo("Watch folder", "Set an input folder first.")
                self.watch_mode.set(False)
                return
            try:
                self._watched_files = set(os.listdir(fld))
            except Exception:
                self._watched_files = set()
            self.root.after(1500, self._watch_poll)
            self._log("info", "Watch: started")
        else:
            self._log("info", "Watch: stopped")

    def _watch_poll(self):
        if not self.watch_mode.get():
            return
        fld = self.input_folder.get()
        if fld and os.path.isdir(fld):
            try:
                current = set(f for f in os.listdir(fld) if f.lower().endswith(VALID_EXTENSIONS))
            except Exception:
                current = set()
            new = sorted(list(current - self._watched_files))
            if new:
                self._log("info", f"Watch: detected {len(new)} new file(s)")
                self.load_files()
                # attempt auto-convert new files
                if not self._converting:
                    self.start_thread_for_files(new)
                else:
                    self._pending_watch_files.extend(new)
                    self._log("info", f"Watch: queued {len(new)} file(s) for later")
            self._watched_files = current
        self.root.after(1500, self._watch_poll)


# =========================
# CLI HEADLESS MODE
# =========================
def _run_cli(args):
    """Headless batch conversion — no GUI required."""
    import argparse
    parser = argparse.ArgumentParser(
        prog="TexForge",
        description="TexForge headless batch converter. Outputs DDS, PNG, JPG, TGA, BMP, WebP, or SVG.",
    )
    parser.add_argument("input",  help="Input folder containing images")
    parser.add_argument("output", help="Output folder for converted files")
    parser.add_argument("--format", default="DXT5",
                        choices=["DXT1","DXT3","DXT5","BC4_UNORM","BC5_UNORM","BC7_UNORM","R8G8B8A8_UNORM","Auto"],
                        help="DDS compression format (default: DXT5)")
    parser.add_argument("--out-type", default="DDS",
                        choices=["DDS","PNG","JPG","TGA","BMP","WebP","SVG"],
                        help="Output file type (default: DDS)")
    parser.add_argument("--no-mips", action="store_true", help="Disable mipmap generation")
    parser.add_argument("--workers", type=int, default=1,
                        help="Parallel worker count (default: 1)")
    parser.add_argument("--overwrite", choices=["Never","Always","Versioned"], default="Never")
    parser.add_argument("--gpu", action="store_true",
                        help="Use texconv_gpu.exe if present")
    parser.add_argument("--quality", type=int, default=90,
                        help="JPEG quality 1-100 (default: 90)")
    ns = parser.parse_args(args)

    inp = os.path.abspath(ns.input)
    out = os.path.abspath(ns.output)
    if not os.path.isdir(inp):
        print(f"ERROR: input folder not found: {inp}", file=sys.stderr); sys.exit(1)
    os.makedirs(out, exist_ok=True)

    files = sorted(f for f in os.listdir(inp) if f.lower().endswith(VALID_EXTENSIONS))
    if not files:
        print("No valid image files found."); sys.exit(0)

    out_type = ns.out_type
    is_dds   = out_type == "DDS"
    fmt      = ns.format
    mips     = not ns.no_mips
    workers  = max(1, ns.workers)
    overwrite = ns.overwrite
    quality  = ns.quality

    # resolve texconv binary
    texconv_bin = os.path.join(APP_DIR, TEXCONV_PATH)
    if ns.gpu:
        gpu_path = os.path.join(APP_DIR, "texconv_gpu.exe")
        if os.path.exists(gpu_path):
            texconv_bin = gpu_path
        else:
            print("WARNING: texconv_gpu.exe not found, using CPU texconv.", file=sys.stderr)

    if is_dds and not os.path.exists(texconv_bin):
        print(f"ERROR: {texconv_bin} not found.", file=sys.stderr); sys.exit(1)

    EXT_MAP = {"DDS": ".dds", "SVG": ".svg", "JPG": ".jpg", "JPEG": ".jpg"}
    out_ext = EXT_MAP.get(out_type, f".{out_type.lower()}")

    import threading, concurrent.futures as cf
    write_lock = threading.Lock()
    done_n = fail_n = 0
    manifest = []

    def _cli_convert(fname):
        src  = os.path.join(inp, fname)
        stem = os.path.splitext(fname)[0]
        extn = os.path.splitext(fname)[1]
        dst  = os.path.join(out, stem + out_ext)

        with write_lock:
            if os.path.exists(dst):
                if overwrite == "Never":
                    return (fname, "SKIP", "", "already exists")
                elif overwrite == "Versioned":
                    base, e2 = os.path.splitext(dst)
                    n = 1
                    while os.path.exists(f"{base}_v{n}{e2}"): n += 1
                    dst = f"{base}_v{n}{e2}"

        try:
            if is_dds:
                file_fmt = fmt
                if fmt == "Auto":
                    try:
                        p = Image.open(src)
                        has_a = "A" in p.getbands() and p.getchannel("A").getextrema()[0] < 255
                    except Exception:
                        has_a = True
                    file_fmt = "DXT5" if has_a else "DXT1"
                cmd = [texconv_bin, "-f", file_fmt, "-o", out, "-y"]
                if not mips: cmd += ["-m", "1"]
                cmd.append(src)
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    return (fname, "FAIL", file_fmt, proc.stderr.strip() or f"exit {proc.returncode}")
                return (fname, "OK", file_fmt, "")
            elif out_type == "SVG":
                save_as_svg(Image.open(src), dst)
                return (fname, "OK", "SVG", "")
            else:
                img = Image.open(src)
                pil_fmt = "JPEG" if out_type in ("JPG","JPEG") else out_type
                if pil_fmt == "JPEG" and img.mode in ("RGBA","LA","P"):
                    img = img.convert("RGB")
                kw = {"quality": quality, "optimize": True} if pil_fmt == "JPEG" else {}
                img.save(dst, format=pil_fmt, **kw)
                return (fname, "OK", out_type, "")
        except Exception as e:
            return (fname, "FAIL", out_type, str(e))

    total = len(files)
    print(f"Converting {total} file(s) → {out_type}  workers={workers}")

    run = cf.ThreadPoolExecutor(max_workers=workers).map(_cli_convert, files)
    for fname, status, fmt_used, reason in run:
        icon = "✔" if status == "OK" else ("–" if status == "SKIP" else "✘")
        print(f"  {icon} [{status}] {fname}" + (f"  ({reason})" if reason else ""))
        if status in ("OK", "SKIP"): done_n += 1
        else: fail_n += 1
        manifest.append({"file": fname, "status": status, "format": fmt_used, "reason": reason})

    manifest_path = os.path.join(out, "export_manifest.json")
    try:
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump({"generated": datetime.now().isoformat(),
                       "total": total, "done": done_n, "failed": fail_n,
                       "entries": manifest}, mf, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"WARNING: manifest write failed: {e}", file=sys.stderr)

    print(f"\nDone  ✔ {done_n}  ✘ {fail_n}  manifest → {manifest_path}")
    sys.exit(0 if fail_n == 0 else 1)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    # If --cli is the first argument, run headless and skip the GUI entirely
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        _run_cli(sys.argv[2:])

    root = tk.Tk()
    try:
        app = DDSConverterApp(root)
        root.mainloop()
    except Exception:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr, flush=True)
        try:
            with open(CRASH_LOG, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n{datetime.now():%Y-%m-%d %H:%M:%S}\n{tb}")
        except Exception:
            pass
        raise