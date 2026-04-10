"""
Image recolor utility
=====================
Generate color-variant images from a source picture and loop-verify outputs.

Example:
    python image_recolor.py --url https://github.com/user-attachments/assets/a0fd8357-be7a-4915-96da-a05d1570d7ac
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
from typing import Iterable

try:
    import requests
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit("Missing dependency: requests. Install with `pip install requests`.") from exc

try:
    from PIL import Image, ImageChops, ImageStat
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit("Missing dependency: Pillow. Install with `pip install Pillow`.") from exc

DEFAULT_IMAGE_URL = "https://github.com/user-attachments/assets/a0fd8357-be7a-4915-96da-a05d1570d7ac"


def _add_bool_arg(parser: argparse.ArgumentParser, flag: str, *, default: bool, help: str) -> None:
    dest = flag.lstrip("-").replace("-", "_")
    if hasattr(argparse, "BooleanOptionalAction"):
        parser.add_argument(flag, action=argparse.BooleanOptionalAction, default=default, help=help)
    else:
        parser.add_argument(
            flag,
            dest=dest,
            action="store_const",
            const=True,
            default=default,
            help=f"Enable: {help}",
        )
        parser.add_argument(
            f"--no-{dest.replace('_', '-')}",
            dest=dest,
            action="store_const",
            const=False,
            help=f"Disable: {help}",
        )


def _download_image(url: str, *, timeout: int = 20) -> Image.Image:
    if not url:
        raise ValueError("Image URL cannot be empty.")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content)).convert("RGB")


def _load_local_image(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Image path not found: {path}")
    return Image.open(path).convert("RGB")


def _hue_shifts(count: int) -> Iterable[int]:
    if count <= 0:
        raise ValueError("Variant count must be positive.")
    step = 256 // (count + 1)
    if step == 0:
        raise ValueError("Variant count too large for hue shifting.")
    return [step * (idx + 1) for idx in range(count)]


def _shift_hue(image: Image.Image, shift: int) -> Image.Image:
    shift = shift % 256
    hsv = image.convert("HSV")
    h, s, v = hsv.split()
    h = h.point(lambda p: (p + shift) % 256)
    return Image.merge("HSV", (h, s, v)).convert("RGB")


def _verify_variants(original: Image.Image, variants: Iterable[tuple[Path, Image.Image]]) -> None:
    for path, variant in variants:
        if not path.exists():
            raise FileNotFoundError(f"Missing output file: {path}")
        if variant.size != original.size:
            raise ValueError(f"Size mismatch: {path} {variant.size} != {original.size}")
        diff = ImageChops.difference(original, variant)
        if diff.getbbox() is None:
            raise ValueError(f"Variant is identical to source: {path}")
        diff_mean = ImageStat.Stat(diff).mean
        if max(diff_mean) < 2.0:
            raise ValueError(f"Variant difference too small: {path} (mean diff {diff_mean})")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate color-variant images and verify outputs.")
    parser.add_argument("--url", default=DEFAULT_IMAGE_URL, help="Source image URL.")
    parser.add_argument("--input", type=Path, help="Local image path (overrides --url).")
    parser.add_argument("--output-dir", type=Path, default=Path("recolor_outputs"))
    parser.add_argument("--variants", type=int, default=6, help="Number of color variants to generate.")
    _add_bool_arg(parser, "--verify", default=True, help="Verify output images in a loop.")
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    if args.input:
        original = _load_local_image(args.input)
    else:
        original = _download_image(args.url)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[tuple[Path, Image.Image]] = []
    for idx, shift in enumerate(_hue_shifts(args.variants), start=1):
        recolored = _shift_hue(original, shift)
        out_path = output_dir / f"variant_{idx:02d}_hue_{shift}.png"
        recolored.save(out_path)
        generated.append((out_path, recolored))
        print(f"✅ Generated: {out_path}")

    if args.verify:
        _verify_variants(original, generated)
        print("✅ Verification passed for all variants.")


if __name__ == "__main__":
    main()
