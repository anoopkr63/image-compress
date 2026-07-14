#!/Users/anoopkr/Desktop/compress/.venv/bin/python3
"""
╔══════════════════════════════════════╗
║       ImagePress — CLI Compressor    ║
╚══════════════════════════════════════╝
Compress images, or convert PDF pages to images and compress them.
Supports JPEG, PNG, WEBP. Runs entirely locally.

Run with the wrapper for a simpler command:
  ./compress image.jpg
  ./compress doc.pdf

Or directly:
  .venv/bin/python3 compress.py image.jpg -q 85
  .venv/bin/python3 compress.py doc.pdf                  # all pages, 200 DPI
  .venv/bin/python3 compress.py doc.pdf --pages 1-3      # only pages 1–3
  .venv/bin/python3 compress.py doc.pdf --dpi 300 -f png # high-res PNG
  .venv/bin/python3 compress.py image.jpg -o out.webp    # convert format
  .venv/bin/python3 compress.py image.jpg -w 1280        # resize width
  .venv/bin/python3 compress.py --batch ./photos -q 85   # batch folder

Quality guide for JPEG:
  90–100  Excellent — use for printing or archiving
  85      Great — recommended default
  75–84   Good — email / sharing
  < 75    Visible grain / blockiness — not recommended
"""

import argparse
import sys
from pathlib import Path

# ── Colours ───────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
PURPLE = "\033[95m"
WHITE  = "\033[97m"

def c(text, *codes):
    return "".join(codes) + str(text) + RESET

def banner():
    print()
    print(c("  ╔══════════════════════════════════════╗", CYAN, BOLD))
    print(c("  ║    ", CYAN, BOLD) + c("ImagePress", PURPLE, BOLD) + c(" — CLI Compressor    ║", CYAN, BOLD))
    print(c("  ╚══════════════════════════════════════╝", CYAN, BOLD))
    print(c("  Images & PDFs · Compress · Convert · Resize\n", DIM))

def quick_hints():
    """Print a plain-English option guide with examples for every flag."""
    W = 14  # label column width
    LINE = "─" * 60

    # ── Options table ──
    print(c(f"  ┌── Options {LINE}┐", DIM))

    rows = [
        ("-q 85",       "Quality",    "1 = smallest file  →  100 = best quality  (default: 92)"),
        ("-f webp",     "Format",     "jpeg  ·  png  ·  webp   (webp = best size & quality balance)"),
        ("-w 1280",     "Width",      "resize output width in px  — height adjusts automatically"),
        ("-H 720",      "Height",     "resize output height in px — width adjusts automatically"),
        ("--no-lock",   "Free resize","use -w and -H together without keeping aspect ratio"),
        ("-o out.jpg",  "Output",     "set a custom output file name or folder"),
        ("--dpi 300",   "PDF DPI",    "150 = normal  ·  200 = sharp (default)  ·  300 = print"),
        ("--pages 1-3", "PDF Pages",  "convert only certain pages: 1  or  1-5  or  1,3,7"),
        ("--batch DIR", "Batch",      "compress every image in a folder at once"),
        ("--info",      "Help",       "show this options guide and exit"),
    ]

    for flag, label, desc in rows:
        flag_str  = c(f"{flag:<14}", CYAN, BOLD)
        label_str = c(f"{label:<{W}}", WHITE)
        print(f"  │  {flag_str} {label_str}  {c(desc, DIM)}")

    print(c(f"  └{LINE}──┘", DIM))

    # ── Examples ──
    print(c("\n  ── Examples ──────────────────────────────────────────────────────", DIM))

    examples = [
        ("Compress image (default quality 92)",         "imgpress photo.jpg"),
        ("Compress at quality 85",                      "imgpress photo.jpg -q 85"),
        ("Convert to WebP format",                      "imgpress photo.jpg -f webp"),
        ("Convert to WebP at quality 85",               "imgpress photo.jpg -q 85 -f webp"),
        ("Resize to 1280px wide (height auto)",         "imgpress photo.jpg -w 1280"),
        ("Resize to exactly 1280×720 (free size)",      "imgpress photo.jpg -w 1280 -H 720 --no-lock"),
        ("Save with a custom file name",                "imgpress photo.jpg -o my_output.jpg"),
        ("PDF → images (all pages, default 200 DPI)",   "imgpress document.pdf"),
        ("PDF at print quality (300 DPI)",              "imgpress document.pdf --dpi 300"),
        ("PDF specific pages only",                     "imgpress document.pdf --pages 1-3"),
        ("PDF → PNG at high quality",                   "imgpress document.pdf -f png -q 95 --dpi 300"),
        ("Batch compress all images in a folder",       "imgpress --batch samples/"),
        ("Batch at quality 80, resize to 1920px wide",  "imgpress --batch samples/ -q 80 -w 1920"),
    ]

    for desc, cmd in examples:
        print(f"  {c('›', PURPLE)}  {c(desc + ':', DIM)}")
        print(f"       {c(cmd, WHITE, BOLD)}\n")


def info(msg):    print(c("  ℹ  ", CYAN) + msg)
def ok(msg):      print(c("  ✔  ", GREEN) + msg)
def warn(msg):    print(c("  ⚠  ", YELLOW) + msg)
def err(msg):     print(c("  ✖  ", RED) + msg)
def section(msg): print(c(f"\n  ── {msg} ", DIM) + c("─" * max(0, 38 - len(msg)), DIM))

def human_size(n_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"

def progress_bar(ratio, width=28):
    filled = int(ratio * width)
    return c("█" * filled + "░" * (width - filled), PURPLE)

# ── Dependency checks ─────────────────────────────────────────────────────────
def require_pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        err("Pillow is not installed.")
        print(c("    pip install Pillow\n", BOLD))
        sys.exit(1)

def require_fitz():
    try:
        import fitz
        return fitz
    except ImportError:
        err("pymupdf is not installed (needed for PDF support).")
        print(c("    pip install pymupdf\n", BOLD))
        sys.exit(1)

# ── Interactive prompts ────────────────────────────────────────────────────────
def prompt(question, default=""):
    hint = f" [{c(default, CYAN)}]" if default else ""
    try:
        answer = input(c(f"  › {question}{hint}: ", WHITE)).strip()
    except (KeyboardInterrupt, EOFError):
        print(); sys.exit(0)
    return answer if answer else default

def prompt_int(question, default, lo=1, hi=10000):
    while True:
        raw = prompt(question, str(default))
        try:
            val = int(raw)
            if lo <= val <= hi:
                return val
            warn(f"Enter a number between {lo} and {hi}.")
        except ValueError:
            warn("Enter a valid whole number.")

def prompt_choice(question, choices, default):
    opts = "/".join(
        c(ch.upper(), CYAN, BOLD) if ch == default else ch for ch in choices
    )
    while True:
        raw = prompt(f"{question} ({opts})", default).lower()
        if raw in choices:
            return raw
        warn(f"Choose one of: {', '.join(choices)}")

def prompt_yn(question, default=True):
    return prompt_choice(question, ["y", "n"], "y" if default else "n") == "y"

# ── Page range parser ─────────────────────────────────────────────────────────
def parse_pages(spec: str, total: int) -> list:
    """Parse '1', '1-5', '1,3,5-7' into a 0-based index list."""
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a) - 1, int(b)))
        else:
            pages.add(int(part) - 1)
    return sorted(p for p in pages if 0 <= p < total)

# ── Output directory helpers ──────────────────────────────────────────────────
OUTPUT_DIR = Path("output")   # always relative to where the script is run

def default_image_out(src: Path, ext_out: str) -> Path:
    """Default output path for a single image: output/<stem>_compressed<ext>"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR / (src.stem + "_compressed" + ext_out)

def default_pdf_out(src: Path) -> Path:
    """Default output folder for a PDF: output/<stem>_pages/"""
    d = OUTPUT_DIR / (src.stem + "_pages")
    return d

# ── Image compression core ─────────────────────────────────────────────────────
FORMAT_MAP = {
    ".jpg": "JPEG", ".jpeg": "JPEG",
    ".png": "PNG",  ".webp": "WEBP",
    ".bmp": "BMP",  ".gif":  "GIF",
}
SAVE_OPTS = {
    "JPEG": {"optimize": True, "progressive": True, "subsampling": 0},
    "PNG":  {"optimize": True},
    "WEBP": {"method": 6},
}

def compress_image(Image, src, dst, quality, width, height, lock_ratio, fmt,
                   sharpen=False):
    from PIL import ImageFilter
    img = Image.open(src) if not hasattr(src, "mode") else src

    # Mode conversion
    if fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
        if img.mode == "P":
            img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    elif fmt in ("PNG", "WEBP") and img.mode == "P":
        img = img.convert("RGBA")

    orig_w, orig_h = img.size
    new_w, new_h = orig_w, orig_h

    # Resize
    if width or height:
        if lock_ratio:
            if width and not height:
                r = width / orig_w;  new_w, new_h = width, max(1, int(orig_h * r))
            elif height and not width:
                r = height / orig_h; new_w, new_h = max(1, int(orig_w * r)), height
            else:
                r = min(width / orig_w, height / orig_h)
                new_w, new_h = max(1, int(orig_w * r)), max(1, int(orig_h * r))
        else:
            new_w, new_h = width or orig_w, height or orig_h
        if (new_w, new_h) != (orig_w, orig_h):
            img = img.resize((new_w, new_h), Image.LANCZOS)

    # Mild unsharp mask sharpening (used after PDF render to recover crispness)
    if sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=2))

    # Save
    opts = dict(SAVE_OPTS.get(fmt, {}))
    if fmt == "WEBP":
        opts["lossless"] = True if quality == 100 else False
        if quality != 100: opts["quality"] = quality
    elif fmt == "JPEG":
        opts["quality"] = quality
    elif fmt == "PNG":
        opts["compress_level"] = max(0, min(9, 9 - round(quality / 100 * 9)))

    img.save(dst, format=fmt, **opts)
    return {"orig_w": orig_w, "orig_h": orig_h, "new_w": new_w, "new_h": new_h}

# ── PDF → images ──────────────────────────────────────────────────────────────
def compress_pdf(fitz, Image, src: Path, out_dir: Path, quality: int,
                 dpi: int, pages_spec,
                 width, height, lock_ratio, fmt: str):
    """Render each PDF page to a sharp image and compress it."""
    from PIL import ImageFilter

    # Warn about quality settings that produce visible grain
    if fmt == "JPEG" and quality < 75:
        warn(f"JPEG quality {quality} is low — output may look grainy.")
        warn("Recommended: 85–95 for clean output. Use WEBP for smaller files at same quality.")
        print()

    doc = fitz.open(str(src))
    total_pages = len(doc)

    if pages_spec:
        page_indices = parse_pages(pages_spec, total_pages)
        if not page_indices:
            err(f"No valid pages in '{pages_spec}' (PDF has {total_pages} page(s)).")
            sys.exit(1)
    else:
        page_indices = list(range(total_pages))

    out_dir.mkdir(parents=True, exist_ok=True)
    ext_map = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
    ext = ext_map.get(fmt, ".jpg")
    pad = len(str(total_pages))
    total_comp = 0

    info(f"PDF pages  : {total_pages}  (rendering {len(page_indices)})")
    info(f"DPI        : {dpi}")
    info(f"Format     : {fmt}  |  Quality : {quality}")
    info(f"Output dir : {c(str(out_dir), CYAN)}")
    print()

    for idx in page_indices:
        page = doc[idx]

        # Render at 2× then downscale for superior anti-aliasing
        # when DPI <= 200; at higher DPI render directly to avoid huge intermediates
        if dpi <= 200:
            render_dpi = dpi * 2
            downscale = True
        else:
            render_dpi = dpi
            downscale = False

        mat = fitz.Matrix(render_dpi / 72, render_dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)
        pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Downscale with LANCZOS for smooth, grain-free result
        if downscale:
            target_w = int(pix.width / 2)
            target_h = int(pix.height / 2)
            pil_img = pil_img.resize((target_w, target_h), Image.LANCZOS)

        dst = out_dir / f"{src.stem}_page_{str(idx + 1).zfill(pad)}{ext}"

        # sharpen=True recovers crispness lost during downscale / PDF rasterisation
        meta = compress_image(Image, pil_img, dst, quality,
                              width, height, lock_ratio, fmt, sharpen=True)
        comp_bytes = dst.stat().st_size
        total_comp += comp_bytes

        print(
            f"  {c('✔', GREEN)}  Page {str(idx + 1).zfill(pad)}  "
            f"{meta['new_w']} × {meta['new_h']} px  →  "
            f"{c(human_size(comp_bytes), CYAN)}"
        )

    doc.close()

    section("PDF Summary")
    ok(f"Pages rendered : {len(page_indices)}")
    ok(f"Total size     : {c(human_size(total_comp), GREEN, BOLD)}")
    ok(f"Output dir     : {c(str(out_dir), CYAN)}")
    print()

# ── Interactive mode ───────────────────────────────────────────────────────────
def interactive_mode(Image, fitz):
    section("Input File")
    while True:
        src_str = prompt("Path to image or PDF")
        src = Path(src_str).expanduser()
        if src.is_file():
            break
        err(f"File not found: {src}")

    is_pdf = src.suffix.lower() == ".pdf"

    section("Output Format")
    fmt_choice = prompt_choice("Format", ["jpeg", "png", "webp"], "jpeg")
    ext_out = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}[fmt_choice]
    fmt = fmt_choice.upper()

    quality = prompt_int("Quality (1–100)", 92, 1, 100)

    if is_pdf:
        dpi = prompt_int("DPI resolution (72–600)  [200=sharp, 300=print]", 200, 72, 600)
        pages_raw = prompt("Pages to render (e.g. 1-3, 1,2,5 or blank for all)", "")
        pages_spec = pages_raw.strip() or None
        out_dir = default_pdf_out(src)
        out_str = prompt("Output folder", str(out_dir))
        out_dir = Path(out_str).expanduser()
        return src, out_dir, quality, None, None, True, fmt, is_pdf, dpi, pages_spec

    # Image path
    out_str = prompt("Save to", str(default_image_out(src, ext_out)))
    dst = Path(out_str).expanduser()

    do_resize = prompt_yn("Resize output?", default=False)
    width = height = None
    lock_ratio = True
    if do_resize:
        try:
            tmp = Image.open(src); ow, oh = tmp.size; tmp.close()
            info(f"Original: {ow} × {oh} px")
        except Exception:
            pass
        w_str = prompt("Width  in px (blank = auto)", "")
        h_str = prompt("Height in px (blank = auto)", "")
        width  = int(w_str) if w_str.isdigit() else None
        height = int(h_str) if h_str.isdigit() else None
        if width or height:
            lock_ratio = prompt_yn("Lock aspect ratio?", default=True)

    return src, dst, quality, width, height, lock_ratio, fmt, is_pdf, 150, None

# ── CLI parser ─────────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        prog="compress",
        description="ImagePress — compress images or convert PDF pages to images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input",            nargs="?",  help="Input image or PDF path")
    p.add_argument("-o", "--output",               help="Output path or folder (for PDFs)")
    p.add_argument("-q", "--quality",  type=int,   default=92, help="Quality 1–100 (default 92)")
    p.add_argument("-w", "--width",    type=int,   help="Output width in pixels")
    p.add_argument("-H", "--height",   type=int,   help="Output height in pixels")
    p.add_argument("--no-lock",        action="store_true", help="Don't lock aspect ratio")
    p.add_argument("-f", "--format",   choices=["jpeg", "png", "webp"], help="Output format")
    p.add_argument("--dpi",            type=int,   default=200, help="DPI for PDF rendering (default 200)")
    p.add_argument("--pages",          metavar="RANGE", help="PDF pages: '1', '1-5', '1,3,5-7'")
    p.add_argument("--info",           action="store_true", help="Show all options with descriptions and exit")
    p.add_argument("--batch",          metavar="DIR",   help="Compress all images in a directory")
    return p

def resolve_image_paths(args):
    given = Path(args.input).expanduser()

    # Auto-search samples/ if not found directly
    if not given.is_file():
        candidate = Path("samples") / given
        if candidate.is_file():
            src = candidate
            info(f"Found in samples/ → {src}")
        else:
            err(f"File not found: {given}")
            # Suggest what's in samples/
            avail = [f.name for f in Path("samples").iterdir()] if Path("samples").is_dir() else []
            if avail:
                print(c(f"  Files in samples/ : {', '.join(avail)}", DIM))
            sys.exit(1)
    else:
        src = given

    is_pdf = src.suffix.lower() == ".pdf"

    if args.format:
        ext_out = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}[args.format]
        fmt = args.format.upper()
    else:
        if is_pdf:
            fmt, ext_out = "JPEG", ".jpg"
        else:
            ext_out = src.suffix.lower() if src.suffix.lower() in FORMAT_MAP else ".jpg"
            fmt = FORMAT_MAP.get(src.suffix.lower(), "JPEG")

    if is_pdf:
        out_dir = Path(args.output).expanduser() if args.output else default_pdf_out(src)
        return src, out_dir, args.quality, args.width, args.height, not args.no_lock, fmt, True, args.dpi, args.pages

    dst = Path(args.output).expanduser() if args.output else default_image_out(src, ext_out)
    if args.output:
        out_ext = dst.suffix.lower()
        if out_ext in FORMAT_MAP:
            fmt = FORMAT_MAP[out_ext]
    return src, dst, args.quality, args.width, args.height, not args.no_lock, fmt, False, args.dpi, args.pages

# ── Batch mode ─────────────────────────────────────────────────────────────────
def batch_compress(Image, directory, quality, args):
    d = Path(directory).expanduser()
    if not d.is_dir():
        err(f"Directory not found: {d}"); sys.exit(1)

    images = [f for f in sorted(d.iterdir()) if f.suffix.lower() in FORMAT_MAP]
    if not images:
        warn("No supported images found in directory."); sys.exit(0)

    out_dir = OUTPUT_DIR / "batch"
    out_dir.mkdir(parents=True, exist_ok=True)
    info(f"Found {len(images)} image(s) — saving to {c(str(out_dir), CYAN)}/\n")

    total_orig = total_comp = 0
    for img_path in images:
        ext = img_path.suffix.lower()
        fmt = FORMAT_MAP.get(ext, "JPEG")
        if fmt not in ("JPEG", "PNG", "WEBP"):
            fmt = "JPEG"
        out_ext = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".webp": ".webp"}.get(ext, ".jpg")
        dst = out_dir / (img_path.stem + out_ext)
        orig_bytes = img_path.stat().st_size
        try:
            compress_image(Image, img_path, dst, quality, args.width, args.height, not args.no_lock, fmt)
            comp_bytes = dst.stat().st_size
            total_orig += orig_bytes; total_comp += comp_bytes
            pct = (1 - comp_bytes / orig_bytes) * 100 if orig_bytes else 0
            pct_col = c(f"−{pct:.1f}%", GREEN) if pct > 0 else c(f"+{abs(pct):.1f}%", YELLOW)
            print(f"  {c('✔', GREEN)}  {img_path.name:<32}  {human_size(orig_bytes):>8} → {human_size(comp_bytes):>8}  {pct_col}")
        except Exception as e:
            print(f"  {c('✖', RED)}  {img_path.name}  — {e}")

    section("Batch Summary")
    saved = total_orig - total_comp
    ok(f"Total saved: {c(human_size(saved), GREEN, BOLD)}  ({saved/total_orig*100:.1f}% reduction)" if total_orig else "Done.")
    ok(f"Output dir : {c(str(out_dir), CYAN)}")
    print()

# ── Single image results ───────────────────────────────────────────────────────
def print_results(src, dst, meta, orig_bytes, comp_bytes):
    ratio    = comp_bytes / orig_bytes if orig_bytes else 1
    pct_save = (1 - ratio) * 100
    section("Results")
    print(f"  {'Source :':<12} {src}")
    print(f"  {'Output :':<12} {dst}")
    print()
    print(f"  {c('Dimensions', BOLD):<19} {meta['orig_w']} × {meta['orig_h']} px  →  {meta['new_w']} × {meta['new_h']} px")
    print(f"  {c('File size', BOLD):<19} {human_size(orig_bytes):<14}  →  {human_size(comp_bytes)}")
    print()
    bar = progress_bar(ratio, 28)
    if pct_save > 0:
        print(f"  {bar}  {c(f'Saved {pct_save:.1f}%', GREEN, BOLD)}")
    elif pct_save < 0:
        warn(f"Output is {abs(pct_save):.1f}% larger (try lower quality or a different format)")
    else:
        print(f"  {bar}  No size change")
    print(); ok(f"Saved → {c(str(dst), CYAN)}"); print()

# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    banner()
    Image  = require_pillow()
    fitz   = require_fitz()
    parser = build_parser()
    args   = parser.parse_args()

    # --info: show the options guide and exit
    if args.info:
        quick_hints()
        sys.exit(0)

    # Batch mode (images only)
    if args.batch:
        section("Batch Compression")
        info(f"Directory : {args.batch}  |  Quality : {args.quality}")
        batch_compress(Image, args.batch, args.quality, args)
        return

    # Interactive mode
    if not args.input:
        try:
            result = interactive_mode(Image, fitz)
        except KeyboardInterrupt:
            print(c("\n\n  Cancelled.\n", DIM)); sys.exit(0)
    else:
        result = resolve_image_paths(args)

    src, dst, quality, width, height, lock_ratio, fmt, is_pdf, dpi, pages_spec = result

    if not 1 <= quality <= 100:
        err("Quality must be between 1 and 100."); sys.exit(1)

    # ── PDF mode ──
    if is_pdf:
        section("PDF → Image Conversion")
        compress_pdf(fitz, Image, src, dst, quality, dpi, pages_spec,
                     width, height, lock_ratio, fmt)
        return

    # ── Image mode ──
    section("Compressing")
    info(f"Source  : {src}")
    info(f"Output  : {dst}")
    info(f"Format  : {fmt}  |  Quality : {quality}{'  (lossless)' if quality == 100 else ''}")
    if width or height:
        info(f"Resize  : {width or 'auto'} × {height or 'auto'} px  ({'locked' if lock_ratio else 'free'})")
    print()

    orig_bytes = src.stat().st_size
    try:
        meta = compress_image(Image, src, dst, quality, width, height, lock_ratio, fmt)
    except Exception as e:
        err(f"Compression failed: {e}"); sys.exit(1)

    print_results(src, dst, meta, orig_bytes, dst.stat().st_size)

if __name__ == "__main__":
    main()
