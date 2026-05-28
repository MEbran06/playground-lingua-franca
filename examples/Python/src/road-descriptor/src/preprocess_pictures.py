#!/usr/bin/env python3
"""
Helper script to preprocess the sample images in the pictures folder 
for faster VLM inference. Current images are already preprocessed. I'll keep it here
for future images.

This script rewrites all JPEG images under the local pictures/ directory to:
- downscale them to a maximum side length, and
- re-encode them with a chosen JPEG quality.

"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


DEFAULT_MAX_SIDE = 768
DEFAULT_JPEG_QUALITY = 85


def preprocess_image(path: Path, max_side: int, jpeg_quality: int) -> tuple[int, int, int]:
    """Downscale and re-encode one image in place."""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        width, height = img.size
        scale = min(1.0, max_side / float(max(width, height)))

        if scale < 1.0:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        tmp = tempfile.NamedTemporaryFile(dir=str(path.parent), suffix=".jpg", delete=False)
        tmp_name = tmp.name
        tmp.close()
        try:
            img.save(tmp_name, format="JPEG", quality=jpeg_quality, optimize=True)
            os.replace(tmp_name, path)
        except Exception:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
            raise

    return width, height, img.size[0] * img.size[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pictures-dir",
        default="pictures",
        help="Folder containing the input images (default: pictures).",
    )
    parser.add_argument(
        "--max-side",
        type=int,
        default=DEFAULT_MAX_SIDE,
        help="Maximum pixel side length to keep after resizing (default: 768).",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_JPEG_QUALITY,
        help="JPEG quality to write back with (default: 85).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List the files that would be rewritten without modifying them.",
    )
    args = parser.parse_args(argv)

    pictures_dir = Path(args.pictures_dir).resolve()
    if not pictures_dir.exists():
        print(f"Pictures directory not found: {pictures_dir}", file=sys.stderr)
        return 1

    image_paths = sorted(list(pictures_dir.glob("*.jpg")) + list(pictures_dir.glob("*.jpeg")) + list(pictures_dir.glob("*.png")))
    if not image_paths:
        print(f"No images found in {pictures_dir}", file=sys.stderr)
        return 1

    print(f"Found {len(image_paths)} image(s) in {pictures_dir}")
    if args.dry_run:
        for path in image_paths:
            print(f"Would rewrite: {path}")
        return 0

    for path in image_paths:
        try:
            old_w, old_h, new_pixels = preprocess_image(path, args.max_side, args.quality)
            print(f"Rewrote {path.name}: {old_w}x{old_h} -> {path.stat().st_size} bytes")
        except Exception as exc:
            print(f"Failed to rewrite {path}: {exc}", file=sys.stderr)
            return 1

    print("Done. Images were rewritten in place.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
