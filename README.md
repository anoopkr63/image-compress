# ImagePress — CLI Image & PDF Compressor

> Compress images and convert PDF pages to images — right from your terminal.
> No internet. No uploads. 100% local.

---

## What it does

- **Compress** JPEG, PNG, and WebP images with full quality control
- **Convert PDF pages** to high-quality images at any resolution
- **Resize** images by width, height, or exact dimensions
- **Batch compress** an entire folder of images at once
- All output lands in `output/` — originals are never touched

---

## Requirements

- macOS / Linux / Windows (WSL)
- Python 3.8 or higher
- [Pillow](https://pillow.readthedocs.io/) — image processing
- [pymupdf](https://pymupdf.readthedocs.io/) — PDF rendering

---

## Setup

Two commands. That's it.

```bash
git clone https://github.com/YOUR_USERNAME/imagepress.git
cd imagepress && bash setup.sh
```

**Open a new terminal tab** — `imgpress` is ready.

> **Requirements:** Python 3.8+ must be installed. Get it from [python.org](https://www.python.org/downloads/) if needed.


---

## Quick Start

```bash
# Display the options guide and practical command examples
imgpress --info
```

---

## Usage

### ⭐ See all options — always start here

```bash
imgpress --info
```

Shows every available flag in plain English with 13 real examples. Run this before anything else if you are unsure what to do.

---

### Interactive mode

```bash
imgpress
```

The tool will ask you everything step by step — no flags needed.

---

### Compress an image

| What you want | Command |
|---------------|---------|
| Compress with default quality (92) | `imgpress photo.jpg` |
| Set quality to 85 | `imgpress photo.jpg -q 85` |
| Convert to WebP | `imgpress photo.jpg -f webp` |
| WebP at quality 85 | `imgpress photo.jpg -q 85 -f webp` |
| Convert to PNG (lossless) | `imgpress photo.jpg -f png` |
| Save with a custom name | `imgpress photo.jpg -o my_result.jpg` |

```bash
imgpress photo.jpg
imgpress photo.jpg -q 85
imgpress photo.jpg -f webp
imgpress photo.jpg -q 85 -f webp -o result.webp
```

---

### Resize an image

| What you want | Command |
|---------------|---------|
| Resize width to 1280px (height auto) | `imgpress photo.jpg -w 1280` |
| Resize height to 720px (width auto) | `imgpress photo.jpg -H 720` |
| Exact size 1280×720 (free, no ratio lock) | `imgpress photo.jpg -w 1280 -H 720 --no-lock` |

```bash
imgpress photo.jpg -w 1280
imgpress photo.jpg -H 720
imgpress photo.jpg -w 1280 -H 720 --no-lock
```

---

### Convert a PDF to images

| What you want | Command |
|---------------|---------|
| All pages, JPEG (default) | `imgpress document.pdf` |
| Print-quality resolution | `imgpress document.pdf --dpi 300` |
| Pages 1 to 3 only | `imgpress document.pdf --pages 1-3` |
| Specific pages (1, 4, 7) | `imgpress document.pdf --pages 1,4,7` |
| High-res PNG output | `imgpress document.pdf -f png -q 95 --dpi 300` |
| Save to a custom folder | `imgpress document.pdf -o output/my_folder` |

```bash
imgpress document.pdf
imgpress document.pdf --dpi 300
imgpress document.pdf --pages 1-3
imgpress document.pdf -f png -q 95 --dpi 300
```

Output pages are named: `document_page_1.jpg`, `document_page_2.jpg`, etc.

---

### Batch compress a folder

```bash
imgpress --batch samples/
imgpress --batch samples/ -q 80
imgpress --batch samples/ -q 80 -w 1920
```

Results go to `output/batch/`.

---

## All options

| Flag | What it does | Default |
|------|-------------|---------|
| `input` | Path to image or PDF (also searched in `samples/` automatically) | — |
| `-q`, `--quality` | Quality: 1 = smallest, 100 = best | `92` |
| `-f`, `--format` | Output format: `jpeg`, `png`, `webp` | Same as input |
| `-w`, `--width` | Output width in pixels | Original |
| `-H`, `--height` | Output height in pixels | Original |
| `--no-lock` | Allow free resize (don't lock aspect ratio) | Locked |
| `-o`, `--output` | Custom output file or folder | `output/<name>_compressed.<ext>` |
| `--dpi` | PDF render resolution | `200` |
| `--pages` | PDF pages to convert: `1`, `1-5`, `1,3,7` | All pages |
| `--batch DIR` | Compress all images in a folder | — |
| `--info` | Show all options with examples, then exit | — |

---

## Quality guide

| Value | Best for |
|-------|----------|
| `100` | Lossless (WebP) / maximum quality (JPEG) |
| `92` | Default — high quality, smaller file |
| `85` | Great balance — recommended for most use |
| `75–84` | Good — email, social media |
| `< 75` | Visible grain and blockiness — **not recommended** for JPEG |

> **PNG** is always lossless. The quality value controls compression speed, not image fidelity.

---

## DPI guide (PDF only)

| DPI | Result |
|-----|--------|
| `150` | Readable — smaller file size |
| `200` | Default — sharp, good for sharing |
| `300` | Print quality — larger file |

> The script renders at 2× DPI internally then downscales with LANCZOS for grain-free results.
> An unsharp mask is applied to restore crisp edges.

---

## File structure

```
imagepress/
├── imgpress              ← run this (global command after setup)
├── compress.py           ← main Python script
├── README.md
├── .gitignore
│
├── samples/              ← put your source files here
│   ├── photo.jpg
│   ├── document.pdf
│   └── ...
│
└── output/               ← all results land here automatically
    ├── photo_compressed.jpg
    ├── document_pages/
    │   ├── document_page_1.jpg
    │   └── document_page_2.jpg
    └── batch/
        └── ...
```

> `output/` and `.venv/` are listed in `.gitignore` and will not be pushed to GitHub.

---

## How output is named

| Input | Output |
|-------|--------|
| `photo.jpg` | `output/photo_compressed.jpg` |
| `photo.jpg -f webp` | `output/photo_compressed.webp` |
| `document.pdf` | `output/document_pages/document_page_1.jpg` |
| `--batch samples/` | `output/batch/*.jpg` |

---

## Supported formats

| Input | Extensions |
|-------|-----------|
| Images | `.jpg` `.jpeg` `.png` `.webp` `.bmp` `.gif` |
| Documents | `.pdf` |

**Output:** `jpeg`, `png`, `webp`

---

## Notes

- **Smart File Lookup:** If a file is not found in your current working directory, the script automatically searches inside the `samples/` folder.
- **Search Suggestions:** If the input file is not found anywhere, the script lists all files available inside the `samples/` directory to help you find the correct name.
- **Safety First:** Original files are **never modified** — a new compressed file is created in the `output/` directory.
- **Lossless WEBP:** Setting quality to `100` with the WEBP format saves the image as lossless.
- **High-Quality Resize:** Image resizing utilizes LANCZOS resampling to preserve sharpness and avoid blur.
- **Locked Aspect Ratio:** When resizing, providing only one dimension (width or height) locks the aspect ratio automatically so images don't look stretched.

---

## License

MIT — free to use, modify, and share.

---

## 🗑️ Uninstall / Clean Up

Because all dependencies were installed inside a self-contained virtual environment (`.venv/`), removing them is completely clean and will not affect the rest of your system:

1. **Delete the folder:**
   Simply drag the `imagepress/` folder to the Trash.

2. **Clean your terminal settings (Optional):**
   Open your shell configuration file (e.g., `~/.zshrc` or `~/.bashrc`) and remove the line ending with `# imagepress`.

