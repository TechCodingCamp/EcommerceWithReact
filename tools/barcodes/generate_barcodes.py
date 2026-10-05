#!/usr/bin/env python3
"""Generate barcode labels (PNG + print-ready PDF) from a SKU/barcode/PO csv.

Label layout replicates the approved sample artwork:

    CLL0078 UKMNSGP738TP GY#SIZEL     <- line 1: SIZE SKU
    |||| ||| |||| || ||||| |||        <- Code 128 symbol of the barcode number
          1 8 4 1 2 2                 <- human readable digits, wide tracking
      BMGK20260914#2RS                <- line 4: PO NUMBER

Usage:
    python3 generate_barcodes.py [--csv barcodes.csv] [--outdir out]
"""

import argparse
import csv
import os

import barcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# --- label geometry (pixels, rendered at 300 dpi equivalent) ----------------
LABEL_W, LABEL_H = 1200, 700
MARGIN = 40

TITLE_SIZE = 52          # SIZE SKU line
DIGITS_SIZE = 86         # human readable barcode digits
DIGITS_TRACKING = 18     # extra px between digits (matches sample spacing)
PO_SIZE = 50             # PO NUMBER line

BAR_HEIGHT = 300         # height of the bars themselves
BAR_TARGET_W = 820       # drawn width of the symbol inside the label

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

# --- PDF sheet layout ------------------------------------------------------
PDF_COLS, PDF_ROWS = 2, 5           # 10 labels per A4 page
PDF_MARGIN = 12 * mm
PDF_GUTTER = 8 * mm


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_width(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]


def draw_centered(draw, y, text, font, width=LABEL_W):
    draw.text(((width - text_width(draw, text, font)) / 2, y), text,
              font=font, fill="black")


def draw_tracked(draw, y, text, font, tracking, width=LABEL_W):
    """Draw text with extra spacing between characters, centered."""
    widths = [text_width(draw, ch, font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (width - total) / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill="black")
        x += w + tracking


def render_symbol(code):
    """Return a PIL image of the Code 128 symbol for `code`.

    The module pattern is drawn directly at a whole number of pixels per
    module: resampling a rendered symbol smears the bar edges and makes the
    label unreadable to scanners, so no scaling happens after this point.
    """
    modules = barcode.get("code128", code).build()[0]
    module_px = max(1, round(BAR_TARGET_W / len(modules)))
    width = module_px * len(modules)

    img = Image.new("RGB", (width, BAR_HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    for i, bit in enumerate(modules):
        if bit == "1":
            draw.rectangle([i * module_px, 0,
                            (i + 1) * module_px - 1, BAR_HEIGHT - 1],
                           fill="black")
    return img


def render_label(size_sku, code, po_number):
    label = Image.new("RGB", (LABEL_W, LABEL_H), "white")
    draw = ImageDraw.Draw(label)

    title_font = load_font(TITLE_SIZE)
    digits_font = load_font(DIGITS_SIZE)
    po_font = load_font(PO_SIZE)

    y = MARGIN
    draw_centered(draw, y, size_sku, title_font)
    y += TITLE_SIZE + 34

    bars = render_symbol(code)
    label.paste(bars, (int((LABEL_W - bars.width) / 2), y))
    y += bars.height + 18

    draw_tracked(draw, y, code, digits_font, DIGITS_TRACKING)
    y += DIGITS_SIZE + 26

    draw_centered(draw, y, po_number, po_font)
    return label


def read_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("barcode")]
    for r in rows:
        for key in ("size_sku", "barcode", "po_number"):
            r[key] = r[key].strip()
    return rows


def build_pdf(rows, png_paths, pdf_path):
    pdf = canvas.Canvas(pdf_path, pagesize=A4)
    page_w, page_h = A4
    cell_w = (page_w - 2 * PDF_MARGIN - (PDF_COLS - 1) * PDF_GUTTER) / PDF_COLS
    cell_h = (page_h - 2 * PDF_MARGIN - (PDF_ROWS - 1) * PDF_GUTTER) / PDF_ROWS
    per_page = PDF_COLS * PDF_ROWS

    for index, (row, png) in enumerate(zip(rows, png_paths)):
        slot = index % per_page
        if slot == 0 and index:
            pdf.showPage()
        col, line = slot % PDF_COLS, slot // PDF_COLS
        x = PDF_MARGIN + col * (cell_w + PDF_GUTTER)
        y = page_h - PDF_MARGIN - (line + 1) * cell_h - line * PDF_GUTTER

        pdf.setStrokeColorRGB(0.75, 0.75, 0.75)
        pdf.setLineWidth(0.4)
        pdf.rect(x, y, cell_w, cell_h)

        # fit the label inside the cell, preserving aspect ratio
        pad = 4 * mm
        avail_w, avail_h = cell_w - 2 * pad, cell_h - 2 * pad
        scale = min(avail_w / LABEL_W, avail_h / LABEL_H)
        w, h = LABEL_W * scale, LABEL_H * scale
        pdf.drawImage(png, x + (cell_w - w) / 2, y + (cell_h - h) / 2,
                      width=w, height=h)

        pdf.setFont("Helvetica", 6)
        pdf.setFillColorRGB(0.45, 0.45, 0.45)
        pdf.drawString(x + 2 * mm, y + 2 * mm,
                       f"{index + 1}/{len(rows)}  {row['barcode']}")
        pdf.setFillColorRGB(0, 0, 0)

    pdf.setTitle("Barcode labels")
    pdf.save()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(here, "barcodes.csv"))
    ap.add_argument("--outdir", default=os.path.join(here, "out"))
    ap.add_argument("--pdf", default=None)
    args = ap.parse_args()

    rows = read_rows(args.csv)
    png_dir = os.path.join(args.outdir, "labels")
    os.makedirs(png_dir, exist_ok=True)

    png_paths = []
    for row in rows:
        label = render_label(row["size_sku"], row["barcode"], row["po_number"])
        path = os.path.join(png_dir, f"{row['barcode']}.png")
        label.save(path, dpi=(300, 300))
        png_paths.append(path)
        print(f"label {row['barcode']}  {row['size_sku']}")

    pdf_path = args.pdf or os.path.join(args.outdir, "barcode-labels.pdf")
    build_pdf(rows, png_paths, pdf_path)
    print(f"\n{len(rows)} labels -> {pdf_path}")


if __name__ == "__main__":
    main()
