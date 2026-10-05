# Barcode Label Generation Report

**Date:** 2026-10-05
**Scope:** Generate scannable barcode labels for every code listed in the supplied
SKU sheet, matching the approved sample label artwork, and output a print-ready PDF.

---

## 1. Source data

20 rows were transcribed from the supplied spreadsheet (`Sheet1`, rows 2–21,
columns `SIZE SKU` / `BARCODE` / `PO NUMBER`) into [`barcodes.csv`](barcodes.csv).

| # | SIZE SKU | BARCODE | PO NUMBER |
|---|----------|---------|-----------|
| 1 | CLO4005 UKGKKWCOTP DKBR#SIZEXS | 350439 | 247GK20260814#1 |
| 2 | CLO4005 UKGKKWCOTP DKBR#SIZES | 350440 | 247GK20260814#1 |
| 3 | CLO4005 UKGKKWCOTP DKBR#SIZEM | 350441 | 247GK20260814#1 |
| 4 | CLO4005 UKGKKWCOTP DKBR#SIZEL | 350442 | 247GK20260814#1 |
| 5 | CLO4005 UKGKKWCOTP DKBR#SIZEXL | 350443 | 247GK20260814#1 |
| 6 | CLO4005 UKGKKWCOTR DKBR#SIZEXS | 350444 | 247GK20260814#2 |
| 7 | CLO4005 UKGKKWCOTR DKBR#SIZES | 350445 | 247GK20260814#2 |
| 8 | CLO4005 UKGKKWCOTR DKBR#SIZEM | 350446 | 247GK20260814#2 |
| 9 | CLO4005 UKGKKWCOTR DKBR#SIZEL | 350447 | 247GK20260814#2 |
| 10 | CLO4005 UKGKKWCOTR DKBR#SIZEXL | 350448 | 247GK20260814#2 |
| 11 | CLO4006 UKGKKWCOTP MK#SIZEXS | 350449 | 247GK20260814#3 |
| 12 | CLO4006 UKGKKWCOTP MK#SIZES | 350450 | 247GK20260814#3 |
| 13 | CLO4006 UKGKKWCOTP MK#SIZEM | 350451 | 247GK20260814#3 |
| 14 | CLO4006 UKGKKWCOTP MK#SIZEL | 350452 | 247GK20260814#3 |
| 15 | CLO4006 UKGKKWCOTP MK#SIZEXL | 350453 | 247GK20260814#3 |
| 16 | CLO4006 UKGKKWCOTR MK#SIZEXS | 350454 | 247GK20260814#4 |
| 17 | CLO4006 UKGKKWCOTR MK#SIZES | 350455 | 247GK20260814#4 |
| 18 | CLO4006 UKGKKWCOTR MK#SIZEM | 350456 | 247GK20260814#4 |
| 19 | CLO4006 UKGKKWCOTR MK#SIZEL | 350457 | 247GK20260814#4 |
| 20 | CLO4006 UKGKKWCOTR MK#SIZEXL | 350458 | 247GK20260814#4 |

Barcodes run consecutively from **350439 to 350458** with no gaps or duplicates.
Four PO groups of five sizes each (XS / S / M / L / XL):

| PO | Style | Colour / variant | Barcodes |
|----|-------|------------------|----------|
| 247GK20260814#1 | CLO4005 | UKGKKWCOTP DKBR | 350439–350443 |
| 247GK20260814#2 | CLO4005 | UKGKKWCOTR DKBR | 350444–350448 |
| 247GK20260814#3 | CLO4006 | UKGKKWCOTP MK | 350449–350453 |
| 247GK20260814#4 | CLO4006 | UKGKKWCOTR MK | 350454–350458 |

## 2. Label pattern

The pattern was taken from the supplied sample label
(`CLL0078 UKMNSGP738TP GY#SIZEL` / `184122` / `BMGK20260914#2RS`) and reproduced
as four stacked, centred elements on a white field:

```
          CLO4005 UKGKKWCOTP DKBR#SIZEXS      <- line 1: SIZE SKU (column A)
          ||| || |||| | ||| || |||| |||       <- Code 128 symbol of the barcode
              3 5 0 4 3 9                     <- human-readable digits, wide tracking
            247GK20260814#1                   <- line 4: PO NUMBER (column C)
```

Rendering decisions:

- **Symbology: Code 128.** The sample's bar pattern has variable-width bars with
  no fixed-length check structure, which rules out UPC/EAN, and the 6-digit
  payload prints compactly in Code 128's numeric mode. Check digit is computed
  automatically by the encoder.
- **Canvas:** 1200 × 700 px at 300 dpi, giving a label of roughly 102 × 59 mm
  at full size; it is scaled to fit the PDF grid.
- **Bars are drawn directly**, one filled rectangle per module at a whole number
  of pixels per module. An earlier revision rendered the symbol and then resized
  it to fit; that anti-aliased the bar edges and **none of the 20 labels
  decoded**. Drawing at integer module width fixed it (see §4).
- **Quiet zone:** ~190 px of white on each side of the symbol, far above the
  10-module minimum.

## 3. Output

| File | Contents |
|------|----------|
| [`out/barcode-labels.pdf`](out/barcode-labels.pdf) | **Main deliverable.** 2 × A4 pages, 10 labels per page (2 columns × 5 rows), light cut guides, and a small `n/20 + barcode` index in each cell corner. |
| `out/labels/<barcode>.png` | The 20 individual labels at 300 dpi, for reprinting a single tag or feeding a label printer. |
| `generate_barcodes.py` | Generator — reads the CSV, renders labels, builds the PDF. |
| `barcodes.csv` | The source data; edit this and re-run to produce a new batch. |

Labels are laid out in spreadsheet order, so page 1 covers POs #1 and #2 and
page 2 covers POs #3 and #4.

## 4. Verification

Every label was decoded back with an independent reader (`zbar`), not just
rendered:

- **20 / 20 PNG labels** decoded to exactly their source barcode number.
- The PDF was rasterised at 300 dpi and re-scanned: **20 / 20 labels decoded**,
  10 per page, all values matching the sheet.
- Printed X-dimension (narrowest bar) in the PDF is **≈ 0.82 mm**, over three
  times the 0.25 mm practical minimum, so the sheet tolerates printing at
  reduced scale.

## 5. Reproducing

```bash
pip install python-barcode pillow reportlab
cd tools/barcodes
python3 generate_barcodes.py                 # writes out/barcode-labels.pdf
python3 generate_barcodes.py --csv other.csv --outdir out2
```

## 6. Notes and assumptions

- The sample PO (`BMGK20260914#2RS`) carries a trailing `RS` suffix that the
  sheet's PO numbers do not. PO values were printed **exactly as they appear in
  column C**, with no suffix added.
- SKU values were read from a screenshot of the sheet. Please spot-check the two
  style codes (`CLO4005`, `CLO4006`) and the `DKBR` / `MK` variants against the
  source file before committing to a print run.
- The sample label's digits use an OCR-style face that is not available here;
  the human-readable line is set in Liberation Sans with wide tracking to match
  the sample's spacing and weight.
