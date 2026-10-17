"""
combine_charts.py - COMBINE PNG CHARTS INTO SINGLE FIGURES (EDA & ML)
=====================================================================
WHAT IT DOES:
  Utility script: stitches individual PNG charts (EDA or ML) into one
  composite image, arranged in a grid. Useful for the technical report
  where several related plots are shown together.
  Two modes:
    - Normal mode: pick charts from data/charts (EDA) or data/ml_charts (ML)
      and combine the chosen ones into a single grid image.
    - Report mode: rebuild exactly the three combined figures used in the
      technical report, with file names matching the figure numbers.

REQUIRES:
  data/charts/*.png       (EDA charts - produced by eda.py)
  data/ml_charts/*.png    (ML charts - produced by the ML scripts)
  Pillow (PIL) + matplotlib

OUTPUT:
  data/combined/<name>.png by default (grid of combined charts):
   eda.png            report Figure 1 - EDA distributions, 6 charts
   ml_eval.png        report Figure 2 - model evaluation, 3 charts (a/b/c)
   ml_importance.png  report Figure 3 - feature importance, 2 charts (a/b)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent  # project root (one level above scripts/)
DATA = ROOT / "data"

# The three combined figures actually used in the technical report.
# File names match the report figure numbers (fig1 = EDA = Figure 1, etc.).
REPORT_PRESETS = {
    "eda": {
        "source": "charts", "cols": 3, "col_width": 980, "row_height": None, "pad": 26,
        "labels": [],
        "only": ["02_rating_histogram.png", "09_complexity_hist.png", "05_games_per_decade.png",
                 "14_players_bucket.png", "12_top_categories.png", "13_top_mechanics.png"],
        "out": "fig1_eda_distributions.png",
    },
    "ml_eval": {
        "source": "ml_charts", "cols": 3, "col_width": None, "row_height": 560, "pad": 26,
        "labels": ["(a)", "(b)", "(c)"],
        "only": ["06_roc_curves.png", "03_confusion_matrix.png", "04_classifier_vs_baseline.png"],
        "out": "fig2_evaluation.png",
    },
    "ml_importance": {
        "source": "ml_charts", "cols": 2, "col_width": None, "row_height": 560, "pad": 26,
        "labels": ["(a)", "(b)"],
        "only": ["02_feature_importance.png", "05_permutation_importance.png"],
        "out": "fig3_importance.png",
    },
}

# fallback font path list, first hit wins
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]

def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def build(src_dir: Path, cols: int, col_width: int | None, row_height: int | None,
          pad: int, only: list[str], labels: list[str]) -> Image.Image:
    if only:
        files = [src_dir / f for f in only if (src_dir / f).exists()]
    else:
        files = sorted(src_dir.glob("*.png"))

    if not files:
        raise SystemExit(f"No PNG files found in {src_dir}")

    if col_width is None and row_height is None:
        raise SystemExit("Either --col-width or --row-height is required")

    imgs = []
    for f in files:
        im = Image.open(f).convert("RGB")
        w, h = im.size
        if row_height:
            nw = round(row_height * w / h)
            imgs.append(im.resize((nw, row_height), Image.LANCZOS))
        else:
            nh = round(col_width * h / w)
            imgs.append(im.resize((col_width, nh), Image.LANCZOS))

    if row_height:
        # single row of equally tall sub-plots (width follows aspect ratio);
        # labels live in a white band above the plots so they never cover them
        label_band = 44 if labels else 0
        W = sum(im.size[0] for im in imgs) + pad * (cols + 1)
        H = label_band + row_height + pad * 2
        canvas = Image.new("RGB", (W, H), "white")
        y_img = pad + label_band
        x = pad
        for i, im in enumerate(imgs):
            canvas.paste(im, (x, y_img))
            if labels and i < len(labels):
                _draw_label(canvas, labels[i], (x + 6, 8))
            x += im.size[0] + pad
        return canvas

    rows = [imgs[i:i + cols] for i in range(0, len(imgs), cols)]
    row_heights = [max(im.size[1] for im in row) for row in rows]

    W = col_width * cols + pad * (cols + 1)
    H = sum(row_heights) + pad * (len(rows) + 1)
    canvas = Image.new("RGB", (W, H), "white")

    y = pad
    idx = 0
    for row, rh in zip(rows, row_heights):
        x = pad
        for im in row:
            canvas.paste(im, (x, y))
            if labels and idx < len(labels):
                _draw_label(canvas, labels[idx], (x + 14, y + 10))
            idx += 1
            x += col_width + pad
        y += rh + pad
    return canvas


def _draw_label(canvas: Image.Image, text: str, pos: tuple[int, int]) -> None:
    draw = ImageDraw.Draw(canvas)
    font = _load_font(40)
    draw.text(pos, text, fill="black", font=font)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", choices=["all", *REPORT_PRESETS], default=None,
                   help="Rebuild the combined figures used in the technical report")
    p.add_argument("--source", choices=["charts", "ml_charts"], default="charts",
                   help="Which image folder to combine (default: charts)")
    p.add_argument("--cols", type=int, default=3, help="Number of columns (default: 3)")
    p.add_argument("--col-width", type=int, default=None, help="Per-column width in px")
    p.add_argument("--row-height", type=int, default=None, help="Uniform sub-plot height in px (width follows aspect ratio)")
    p.add_argument("--pad", type=int, default=26, help="Gap between images in px (default: 26)")
    p.add_argument("--output", type=Path, default=None,
                   help="Output path (default: data/combined/<source>_combined.png)")
    p.add_argument("--only", nargs="*", default=[],
                   help="Optional: combine only these filenames, in this order")
    args = p.parse_args()

    if args.report:
        names = list(REPORT_PRESETS) if args.report == "all" else [args.report]
        for name in names:
            cfg = REPORT_PRESETS[name]
            src_dir = DATA / cfg["source"]
            if not src_dir.is_dir():
                raise SystemExit(f"Source folder not found: {src_dir}")
            out = DATA / "combined" / cfg["out"]
            out.parent.mkdir(parents=True, exist_ok=True)
            canvas = build(src_dir, cfg["cols"], cfg.get("col_width"), cfg.get("row_height"),
                           cfg["pad"], cfg["only"], cfg.get("labels", []))
            canvas.save(out)
            print(f"report[{name}]: {len(cfg['only'])} charts -> {out} ({canvas.size[0]}x{canvas.size[1]})")
        return

    src_dir = DATA / args.source
    if not src_dir.is_dir():
        raise SystemExit(f"Source folder not found: {src_dir}")

    if args.col_width is None and args.row_height is None:
        args.col_width = 980

    out = args.output or (DATA / "combined" / f"{args.source}_combined.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = build(src_dir, args.cols, args.col_width, args.row_height, args.pad, args.only, [])
    canvas.save(out)
    print(f"Combined {len(list(src_dir.glob('*.png'))) if not args.only else len(args.only)} images -> {out} ({canvas.size[0]}x{canvas.size[1]})")


if __name__ == "__main__":
    main()
