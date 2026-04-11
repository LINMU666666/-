"""
DRIFTS plotting utility
=======================
Generate publication-style DRIFTS plots with peak annotations and looped verification.

Example:
    python drifts_plot.py --file drifts_data.csv
    python drifts_plot.py --input-dir ./data --pattern "*.csv" --output-dir drifts_outputs
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, savgol_filter

# =========================
# SCI plotting style
# =========================
plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 12,
    "axes.linewidth": 1.2,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 5,
    "ytick.major.size": 5,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "xtick.minor.size": 3,
    "ytick.minor.size": 3,
})


def _bi(en: str, cn: str) -> str:
    return f"{en} ({cn})"


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


def read_data_file(file_path: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Auto-read csv / txt / xlsx; use first two columns as x, y.
    """
    ext = file_path.suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in {".txt", ".dat"}:
        try:
            df = pd.read_csv(file_path, sep=None, engine="python")
        except Exception:
            df = pd.read_csv(file_path, delim_whitespace=True, engine="python")
    elif ext in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(_bi(f"Unsupported file type: {ext}", f"不支持的文件格式: {ext}"))

    df = df.dropna()
    x = df.iloc[:, 0].astype(float).to_numpy()
    y = df.iloc[:, 1].astype(float).to_numpy()
    return x, y, df.columns[:2].tolist()


def preprocess_y(y: np.ndarray, smooth_window: int = 11, polyorder: int = 3) -> np.ndarray:
    """
    Smooth y using Savitzky-Golay filter.
    """
    if len(y) < smooth_window:
        return y
    if smooth_window % 2 == 0:
        smooth_window += 1
    return savgol_filter(y, window_length=smooth_window, polyorder=polyorder)


def auto_detect_peaks(
    y: np.ndarray,
    prominence_ratio: float = 0.03,
    distance: int = 30,
) -> tuple[np.ndarray, dict]:
    """
    Auto peak detection on normalized y.
    """
    y_norm = (y - np.min(y)) / (np.max(y) - np.min(y) + 1e-9)
    prominence = prominence_ratio * np.max(y_norm)
    peaks, props = find_peaks(y_norm, prominence=prominence, distance=distance)
    return peaks, props


def _normalize_y(y: np.ndarray) -> np.ndarray:
    span = np.max(y) - np.min(y)
    if span <= 0:
        return y
    return (y - np.min(y)) / span


def _prepare_plot_data(x: np.ndarray, y: np.ndarray, y_smooth: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # DRIFTS typically shows wavenumber from high to low (left to right)
    if x[0] < x[-1]:
        return x[::-1], y[::-1], y_smooth[::-1]
    return x, y, y_smooth


def _plot_drifts(
    *,
    file_path: Path,
    output_dir: Path,
    smooth_window: int,
    polyorder: int,
    prominence_ratio: float,
    distance: int,
    normalize: bool,
    fill_curve: bool,
    show_peaks: bool,
    dpi: int,
) -> list[Path]:
    x, y, _ = read_data_file(file_path)
    y_smooth = preprocess_y(y, smooth_window=smooth_window, polyorder=polyorder)

    if normalize:
        y = _normalize_y(y)
        y_smooth = _normalize_y(y_smooth)

    x_plot, y_plot, y_smooth_plot = _prepare_plot_data(x, y, y_smooth)

    peaks, _ = auto_detect_peaks(
        y_smooth_plot,
        prominence_ratio=prominence_ratio,
        distance=distance,
    )

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(x_plot, y_plot, color="black", lw=1.2, label="Raw data")
    ax.plot(x_plot, y_smooth_plot, color="#d62728", lw=1.8, label="Smoothed")
    if fill_curve:
        ax.fill_between(x_plot, y_smooth_plot, color="#d62728", alpha=0.12)

    if show_peaks:
        y_max = np.max(y_smooth_plot) if len(y_smooth_plot) else 1.0
        for idx, peak in enumerate(peaks, start=1):
            px = x_plot[peak]
            py = y_smooth_plot[peak]
            ax.axvline(px, color="#1f77b4", ls=":", lw=0.9, alpha=0.8)
            ax.text(
                px,
                py + 0.03 * y_max,
                f"{px:.0f}",
                rotation=90,
                ha="center",
                va="bottom",
                fontsize=9,
                color="#1f77b4",
            )

    ax.set_xlabel("Wavenumber (cm$^{-1}$)")
    ax.set_ylabel("Absorbance (a.u.)" if not normalize else "Normalized absorbance (a.u.)")
    ax.set_xlim(x_plot.max(), x_plot.min())
    ax.legend(frameon=False, loc="upper right")
    ax.tick_params(direction="in", top=True, right=True)
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)

    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = file_path.stem
    png_path = output_dir / f"{stem}_drifts.png"
    tif_path = output_dir / f"{stem}_drifts.tif"
    plt.savefig(png_path, dpi=dpi, bbox_inches="tight")
    plt.savefig(tif_path, dpi=max(dpi, 600), bbox_inches="tight")
    plt.close(fig)

    print(_bi(f"✅ DRIFTS saved: {png_path} / {tif_path}", f"✅ DRIFTS图已保存: {png_path} / {tif_path}"))
    if show_peaks and len(peaks) > 0:
        print(_bi(
            f"Detected peaks: {[round(x_plot[p], 2) for p in peaks]}",
            f"识别到峰位: {[round(x_plot[p], 2) for p in peaks]}",
        ))
    return [png_path, tif_path]


def _collect_files(
    *,
    file: Path | None,
    files: Iterable[Path] | None,
    input_dir: Path | None,
    pattern: str,
) -> list[Path]:
    collected: list[Path] = []
    if file:
        collected.append(file)
    if files:
        collected.extend(files)
    if input_dir:
        collected.extend(sorted(input_dir.glob(pattern)))
    unique = sorted({path.resolve() for path in collected})
    if not unique:
        raise ValueError(_bi(
            "Please provide --file / --files or --input-dir + --pattern",
            "请提供 --file / --files 或 --input-dir + --pattern",
        ))
    return unique


def _verify_outputs(paths: Iterable[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing output file: {path}")
        if path.stat().st_size <= 0:
            raise ValueError(f"Output file is empty: {path}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate DRIFTS plots in SCI style.")
    parser.add_argument("--file", type=Path, help="Single data file path.")
    parser.add_argument("--files", type=Path, nargs="+", help="Multiple data file paths.")
    parser.add_argument("--input-dir", type=Path, help="Directory containing data files.")
    parser.add_argument("--pattern", default="*.csv", help="Glob pattern for input-dir.")
    parser.add_argument("--output-dir", type=Path, default=Path("drifts_outputs"))
    parser.add_argument("--smooth-window", type=int, default=11)
    parser.add_argument("--polyorder", type=int, default=3)
    parser.add_argument("--prominence-ratio", type=float, default=0.04)
    parser.add_argument("--distance", type=int, default=35)
    parser.add_argument("--dpi", type=int, default=300)
    _add_bool_arg(parser, "--normalize", default=False, help="Normalize intensity to 0-1.")
    _add_bool_arg(parser, "--fill-curve", default=True, help="Fill under the smoothed curve.")
    _add_bool_arg(parser, "--show-peaks", default=True, help="Annotate detected peaks.")
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    files = _collect_files(
        file=args.file,
        files=args.files,
        input_dir=args.input_dir,
        pattern=args.pattern,
    )

    outputs: list[Path] = []
    for path in files:
        outputs.extend(
            _plot_drifts(
                file_path=path,
                output_dir=args.output_dir,
                smooth_window=args.smooth_window,
                polyorder=args.polyorder,
                prominence_ratio=args.prominence_ratio,
                distance=args.distance,
                normalize=args.normalize,
                fill_curve=args.fill_curve,
                show_peaks=args.show_peaks,
                dpi=args.dpi,
            )
        )

    _verify_outputs(outputs)
    print(_bi("✅ Loop verification completed. All outputs are valid.", "✅ 已完成循环验证，所有输出文件有效。"))


if __name__ == "__main__":
    main()
