# Barcode label generator

Generates scannable Code 128 labels — SIZE SKU on top, barcode, human-readable
digits, PO number underneath — and collects them into a print-ready A4 PDF.

```bash
pip install python-barcode pillow reportlab
python3 generate_barcodes.py
```

Outputs `out/barcode-labels.pdf` (10 labels per page) and one 300 dpi PNG per
label in `out/labels/`.

To generate a different batch, edit [`barcodes.csv`](barcodes.csv) — columns
`size_sku,barcode,po_number` — and re-run. See [REPORT.md](REPORT.md) for the
current batch, the label pattern, and scan verification results.
