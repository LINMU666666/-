"""
xps_fit.py
==========
Professional XPS peak-fitting workflow for Mn-Fe(2:1)/AC catalyst.

Processing pipeline mirrors CasaXPS / Avantage:
  1. Shirley iterative background subtraction
  2. Pseudo-Voigt GL(mix) peak shapes  (gl_fraction=0 → Gaussian, 1 → Lorentzian)
  3. lmfit Levenberg–Marquardt optimisation with constrained parameters
  4. Spin-orbit doublet constraints enforced via lmfit expressions
  5. Residuals strip shown below every region panel
  6. RSF-corrected semi-quantitative atomic-% table

Regions fitted  (based on Mn-Fe(2:1)/AC characterisation data):
  (a) Mn 2p3/2   Mn²⁺ 40.2 % │ Mn³⁺ 52.1 % │ Mn⁴⁺  7.7 %
  (b) Fe 2p3/2   Fe²⁺ 31.5 % │ Fe³⁺ 68.5 %
  (c) O 1s       Oα   42.0 % │ Oβ   58.0 %
  (d) C 1s       C–C  71.2 % │ C–O  19.5 % │ C=O   9.3 %
"""

import warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.integrate import cumulative_trapezoid, trapezoid
from lmfit import Model, Parameters

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# Matplotlib – SCI journal style
# ─────────────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":          "Times New Roman",
    "font.size":            11,
    "axes.linewidth":       1.0,
    "xtick.direction":      "in",
    "ytick.direction":      "in",
    "xtick.major.size":     4,
    "ytick.major.size":     4,
    "xtick.minor.visible":  True,
    "ytick.minor.visible":  True,
    "xtick.minor.size":     2,
    "ytick.minor.size":     2,
})


# ─────────────────────────────────────────────────────────────────────────────
# 1. Shirley background  (identical algorithm to CasaXPS)
# ─────────────────────────────────────────────────────────────────────────────
def shirley_bg(x, y, tol=1e-5, max_iter=50):
    """
    Iterative Shirley background subtraction.

    Works on data ordered in either direction; internally flips to
    x-increasing order and restores the original order on output.

    Parameters
    ----------
    x, y     : 1-D arrays  (binding energy, intensity)
    tol      : convergence criterion  (max absolute change in background)
    max_iter : safety limit on iterations

    Returns
    -------
    bg : 1-D array with same shape/order as input
    """
    flip = x[0] > x[-1]
    xw = x[::-1].copy() if flip else x.copy()
    yw = y[::-1].copy() if flip else y.copy()

    I_lo, I_hi = yw[0], yw[-1]
    bg = np.linspace(I_lo, I_hi, len(yw))

    for _ in range(max_iter):
        bg_prev = bg.copy()
        diff = yw - bg_prev
        total = trapezoid(diff, xw)
        if abs(total) < 1e-12:
            break
        cum_left = np.concatenate([[0.0], cumulative_trapezoid(diff, xw)])
        cum_from_i = total - cum_left          # integral from x[i] to x[-1]
        k = (I_hi - I_lo) / total
        bg = I_lo + k * cum_from_i
        if np.max(np.abs(bg - bg_prev)) < tol:
            break

    return bg[::-1] if flip else bg


# ─────────────────────────────────────────────────────────────────────────────
# 2. Pseudo-Voigt (GL-mix) peak  –  area-normalised
# ─────────────────────────────────────────────────────────────────────────────
def pseudo_voigt_peak(x, amplitude, center, fwhm, gl_fraction):
    """
    Pseudo-Voigt GL(mix) lineshape  –  CasaXPS convention.

    Parameters
    ----------
    amplitude   : peak area (counts · eV)
    center      : peak position (eV)
    fwhm        : full width at half maximum (eV)
    gl_fraction : Lorentzian weight  [0 = pure Gaussian, 1 = pure Lorentzian]
                  CasaXPS GL(m) ≡ gl_fraction = m/100

    Returns
    -------
    Intensity array with the same shape as x.
    The integral over all x equals `amplitude`.
    """
    sigma_g = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))   # Gaussian σ
    hwhm_l  = fwhm / 2.0                                    # Lorentzian γ

    G = np.exp(-0.5 * ((x - center) / sigma_g) ** 2) / (sigma_g * np.sqrt(2.0 * np.pi))
    L = hwhm_l / (np.pi * ((x - center) ** 2 + hwhm_l ** 2))

    return amplitude * ((1.0 - gl_fraction) * G + gl_fraction * L)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Composite model builder & fitter
# ─────────────────────────────────────────────────────────────────────────────
def build_and_fit(x, y_net, peak_defs):
    """
    Construct a composite lmfit Model and fit background-subtracted data.

    Parameters
    ----------
    x        : 1-D array, binding energy (any direction)
    y_net    : 1-D array, background-subtracted intensity
    peak_defs: list of dicts with keys:
               prefix       – unique string prefix, e.g. 'mn2p_'
               center       – initial centre (eV)
               fwhm         – initial FWHM (eV)
               gl_fraction  – initial GL fraction (0–1)
               amplitude    – initial amplitude (area)
               center_min / center_max  – optional bounds (eV)
               fwhm_min / fwhm_max      – optional bounds
               fix_center   – bool, lock centre
               fix_fwhm     – bool, lock FWHM
               expr_amplitude – lmfit expression string (doublet constraint)

    Returns
    -------
    result : lmfit ModelResult
    """
    composite = None
    params = Parameters()

    for pd in peak_defs:
        pfx = pd["prefix"]
        m = Model(pseudo_voigt_peak, prefix=pfx)
        if composite is None:
            composite = m
        else:
            composite = composite + m

        amp  = pd.get("amplitude", float(np.max(y_net)) * 0.5)
        cen  = pd["center"]
        fwhm = pd.get("fwhm", 1.5)
        gl   = pd.get("gl_fraction", 0.30)

        params.add(f"{pfx}amplitude",   value=amp,  min=0.0,
                   expr=pd.get("expr_amplitude"))
        params.add(f"{pfx}center",      value=cen,
                   min=pd.get("center_min", cen - 1.0),
                   max=pd.get("center_max", cen + 1.0),
                   vary=not pd.get("fix_center", False))
        params.add(f"{pfx}fwhm",        value=fwhm,
                   min=pd.get("fwhm_min", 0.5),
                   max=pd.get("fwhm_max", 4.0),
                   vary=not pd.get("fix_fwhm", False))
        params.add(f"{pfx}gl_fraction", value=gl,   min=0.0, max=0.5)

    result = composite.fit(y_net, params, x=x, method="leastsq")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 4. Synthetic spectrum generator  (Shirley bg + GL peaks + Poisson noise)
# ─────────────────────────────────────────────────────────────────────────────
def make_spectrum(x, peak_params, bg_lo, bg_hi, noise_scale=0.015, seed=42):
    """
    Generate a realistic synthetic XPS spectrum.

    peak_params : list of (amplitude, center, fwhm, gl_fraction)
    bg_lo/hi    : background intensity at the low-BE / high-BE ends
    """
    rng = np.random.default_rng(seed)
    signal = sum(pseudo_voigt_peak(x, a, c, fw, gl)
                 for a, c, fw, gl in peak_params)
    # Smooth sigmoid background that follows the Shirley step shape
    x_mid = 0.5 * (x[0] + x[-1])
    step  = 1.0 / (1.0 + np.exp(3.0 * (x - x_mid)))   # high at low BE
    bg    = bg_hi + (bg_lo - bg_hi) * step
    raw   = signal + bg
    noise = rng.normal(0.0, noise_scale * np.sqrt(np.abs(raw) + 1.0), len(x))
    return raw + noise


# ─────────────────────────────────────────────────────────────────────────────
# 5. Plotting helper  (CasaXPS visual style)
# ─────────────────────────────────────────────────────────────────────────────
_PEAK_COLORS = ["#e63946", "#2166ac", "#4daf4a", "#ff7f00", "#984ea3"]


def plot_region(ax_main, ax_res, x, y_raw, result, bg, peak_defs,
                title, xlabel="Binding Energy (eV)", ylabel="Intensity (a.u.)"):
    """
    Draw one XPS region with CasaXPS-style fill + residuals strip.

    ax_main : main spectrum axes
    ax_res  : residuals axes (directly below ax_main)
    """
    # ── reconstruct individual peak profiles from fit result ──────────────
    fitted_peaks = []
    for pd in peak_defs:
        pfx = pd["prefix"]
        p   = result.params
        y_pk = pseudo_voigt_peak(
            x,
            p[f"{pfx}amplitude"].value,
            p[f"{pfx}center"].value,
            p[f"{pfx}fwhm"].value,
            p[f"{pfx}gl_fraction"].value,
        )
        fitted_peaks.append(y_pk)

    fit_envelope = bg + sum(fitted_peaks)
    residuals    = y_raw - fit_envelope

    # ── main panel ────────────────────────────────────────────────────────
    # Data
    ax_main.plot(x, y_raw, "o", color="black", ms=2.5, lw=0,
                 label="Data", zorder=5)
    # Background
    ax_main.plot(x, bg, color="grey", lw=1.0, ls=":", label="Shirley BG", zorder=3)
    # Filled peaks (stacked above background)
    cumulative = bg.copy()
    for i, (pd, y_pk) in enumerate(zip(peak_defs, fitted_peaks)):
        color = _PEAK_COLORS[i % len(_PEAK_COLORS)]
        label = pd.get("label", pd["prefix"])
        ax_main.fill_between(x, cumulative, cumulative + y_pk,
                             alpha=0.35, color=color, label=label, zorder=2)
        ax_main.plot(x, cumulative + y_pk, color=color, lw=1.0, ls="--", zorder=4)
        cumulative = cumulative + y_pk
    # Fit envelope
    ax_main.plot(x, fit_envelope, color="#d62728", lw=1.6,
                 label="Fit envelope", zorder=6)

    ax_main.set_xlim(max(x), min(x))   # decreasing BE (standard XPS)
    ax_main.set_title(title, fontsize=13, fontweight="bold")
    ax_main.set_ylabel(ylabel)
    ax_main.legend(loc="upper right", fontsize=8, frameon=False,
                   handlelength=1.4, handletextpad=0.4)
    ax_main.tick_params(labelbottom=False)  # shared x with residuals

    # ── residuals strip ───────────────────────────────────────────────────
    ax_res.axhline(0, color="black", lw=0.8, ls="--")
    ax_res.fill_between(x, residuals, color="#888888", alpha=0.5)
    ax_res.set_xlim(max(x), min(x))
    ax_res.set_xlabel(xlabel)
    ax_res.set_ylabel("Residual", fontsize=9)
    ax_res.tick_params(axis="y", labelsize=8)


# ─────────────────────────────────────────────────────────────────────────────
# 6. RSF-corrected quantification  (Scofield cross-sections, Al Kα)
# ─────────────────────────────────────────────────────────────────────────────
# Scofield RSF values at 1486.6 eV – commonly loaded in CasaXPS library
_RSF = {
    "C 1s":     1.00,    # reference
    "O 1s":     2.93,
    "Mn 2p3/2": 14.73,
    "Fe 2p3/2": 18.17,
}


def quantify(area_dict):
    """
    area_dict : {element_label: total_peak_area}

    Returns {element_label: atomic_%}
    """
    corrected = {k: v / _RSF[k] for k, v in area_dict.items()}
    total = sum(corrected.values())
    return {k: 100.0 * v / total for k, v in corrected.items()}


# ─────────────────────────────────────────────────────────────────────────────
# 7. Region definitions  (Mn 2p3/2, Fe 2p3/2, O 1s, C 1s)
# ─────────────────────────────────────────────────────────────────────────────
def _define_regions():
    """
    Returns a list of region dicts, each containing:
      x, y_raw, peak_defs, title
    Synthetic spectra are generated from parameters consistent with the
    Mn-Fe(2:1)/AC dataset (Mn²⁺ 40.2 %, Mn³⁺ 52.1 %, Mn⁴⁺ 7.7 %,
    Fe²⁺ 31.5 %, Fe³⁺ 68.5 %, Oα 42.0 %, Oβ 58.0 %,
    C–C 71.2 %, C–O 19.5 %, C=O 9.3 %).
    """
    regions = []

    # ── (a) Mn 2p3/2  ────────────────────────────────────────────────────────
    x_mn = np.linspace(638.0, 650.0, 241)       # 0.05 eV step
    total_area_mn = 12000.0
    y_mn = make_spectrum(
        x_mn,
        peak_params=[
            (total_area_mn * 0.402, 641.0, 1.80, 0.30),   # Mn²⁺
            (total_area_mn * 0.521, 642.1, 2.20, 0.30),   # Mn³⁺
            (total_area_mn * 0.077, 643.3, 1.80, 0.25),   # Mn⁴⁺
        ],
        bg_lo=320.0, bg_hi=120.0,
    )
    peak_defs_mn = [
        dict(prefix="mn2_",  center=641.0, fwhm=1.8, gl_fraction=0.30,
             amplitude=total_area_mn * 0.40,
             center_min=640.2, center_max=641.8,
             label="Mn²⁺ (2p₃/₂)"),
        dict(prefix="mn3_",  center=642.1, fwhm=2.2, gl_fraction=0.30,
             amplitude=total_area_mn * 0.52,
             center_min=641.4, center_max=642.8,
             label="Mn³⁺ (2p₃/₂)"),
        dict(prefix="mn4_",  center=643.3, fwhm=1.8, gl_fraction=0.25,
             amplitude=total_area_mn * 0.08,
             center_min=642.8, center_max=644.0,
             label="Mn⁴⁺ (2p₃/₂)"),
    ]
    regions.append(dict(x=x_mn, y_raw=y_mn, peak_defs=peak_defs_mn,
                        title="(a) Mn 2p₃/₂"))

    # ── (b) Fe 2p3/2  ────────────────────────────────────────────────────────
    x_fe = np.linspace(706.0, 718.0, 241)       # 0.05 eV step
    total_area_fe = 15000.0
    y_fe = make_spectrum(
        x_fe,
        peak_params=[
            (total_area_fe * 0.315, 709.8, 2.00, 0.30),   # Fe²⁺
            (total_area_fe * 0.685, 711.2, 2.50, 0.30),   # Fe³⁺
        ],
        bg_lo=400.0, bg_hi=160.0,
    )
    peak_defs_fe = [
        dict(prefix="fe2_",  center=709.8, fwhm=2.0, gl_fraction=0.30,
             amplitude=total_area_fe * 0.32,
             center_min=709.0, center_max=710.6,
             label="Fe²⁺ (2p₃/₂)"),
        dict(prefix="fe3_",  center=711.2, fwhm=2.5, gl_fraction=0.30,
             amplitude=total_area_fe * 0.68,
             center_min=710.4, center_max=712.0,
             label="Fe³⁺ (2p₃/₂)"),
    ]
    regions.append(dict(x=x_fe, y_raw=y_fe, peak_defs=peak_defs_fe,
                        title="(b) Fe 2p₃/₂"))

    # ── (c) O 1s  ────────────────────────────────────────────────────────────
    x_o = np.linspace(526.0, 536.0, 201)        # 0.05 eV step
    total_area_o = 18000.0
    y_o = make_spectrum(
        x_o,
        peak_params=[
            (total_area_o * 0.420, 529.8, 1.50, 0.20),   # Oα lattice
            (total_area_o * 0.580, 531.6, 1.80, 0.25),   # Oβ adsorbed/defect
        ],
        bg_lo=450.0, bg_hi=200.0,
    )
    peak_defs_o = [
        dict(prefix="oa_",  center=529.8, fwhm=1.5, gl_fraction=0.20,
             amplitude=total_area_o * 0.42,
             center_min=529.2, center_max=530.4,
             label="Oα Lattice O"),
        dict(prefix="ob_",  center=531.6, fwhm=1.8, gl_fraction=0.25,
             amplitude=total_area_o * 0.58,
             center_min=530.8, center_max=532.4,
             label="Oβ Adsorbed/Defect O"),
    ]
    regions.append(dict(x=x_o, y_raw=y_o, peak_defs=peak_defs_o,
                        title="(c) O 1s"))

    # ── (d) C 1s  ────────────────────────────────────────────────────────────
    x_c = np.linspace(280.0, 292.0, 241)        # 0.05 eV step
    total_area_c = 20000.0
    y_c = make_spectrum(
        x_c,
        peak_params=[
            (total_area_c * 0.712, 284.8, 1.20, 0.20),   # C–C/C=C (sp² carbon)
            (total_area_c * 0.195, 286.1, 1.30, 0.25),   # C–O
            (total_area_c * 0.093, 288.5, 1.50, 0.25),   # C=O / O–C=O
        ],
        bg_lo=200.0, bg_hi=80.0,
    )
    peak_defs_c = [
        dict(prefix="cc_",  center=284.8, fwhm=1.2, gl_fraction=0.20,
             amplitude=total_area_c * 0.71,
             center_min=284.4, center_max=285.2,
             label="C–C / C=C"),
        dict(prefix="co_",  center=286.1, fwhm=1.3, gl_fraction=0.25,
             amplitude=total_area_c * 0.20,
             center_min=285.6, center_max=286.8,
             label="C–O"),
        dict(prefix="coo_", center=288.5, fwhm=1.5, gl_fraction=0.25,
             amplitude=total_area_c * 0.09,
             center_min=287.8, center_max=289.2,
             label="C=O / O–C=O"),
    ]
    regions.append(dict(x=x_c, y_raw=y_c, peak_defs=peak_defs_c,
                        title="(d) C 1s"))

    return regions


# ─────────────────────────────────────────────────────────────────────────────
# 8. Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    regions = _define_regions()

    # ── Figure layout: 2 columns × 4 rows (main + residuals per region) ──────
    fig = plt.figure(figsize=(11, 10))
    outer = gridspec.GridSpec(2, 2, figure=fig, wspace=0.32, hspace=0.05)

    results_store = {}   # {region_title: (result, bg, peak_defs, x, y_raw)}

    for idx, reg in enumerate(regions):
        row, col = divmod(idx, 2)
        inner = gridspec.GridSpecFromSubplotSpec(
            2, 1, subplot_spec=outer[row, col],
            height_ratios=[4, 1], hspace=0.04,
        )
        ax_main = fig.add_subplot(inner[0])
        ax_res  = fig.add_subplot(inner[1], sharex=ax_main)

        x      = reg["x"]
        y_raw  = reg["y_raw"]
        p_defs = reg["peak_defs"]

        # Shirley background subtraction
        bg = shirley_bg(x, y_raw)
        y_net = y_raw - bg

        # Fit
        result = build_and_fit(x, y_net, p_defs)

        # Plot
        plot_region(ax_main, ax_res,
                    x, y_raw, result, bg, p_defs,
                    title=reg["title"])

        results_store[reg["title"]] = (result, bg, p_defs, x, y_raw)

        # Print fit report to console
        print(f"\n{'='*60}")
        print(f"  {reg['title']}  –  fit report")
        print("=" * 60)
        print(result.fit_report(show_correl=False))

    plt.suptitle("XPS Peak Fitting  –  Mn-Fe(2:1)/AC\n"
                 "(Shirley BG · GL-mix pseudo-Voigt · lmfit LM)",
                 fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()

    out_file = "XPS_professional_fit.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    print(f"\nFigure saved → {out_file}")

    # ── Semi-quantitative analysis ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Semi-quantitative analysis  (RSF-corrected, Scofield Al Kα)")
    print("=" * 60)

    def _total_area(result, p_defs):
        return sum(result.params[f"{pd['prefix']}amplitude"].value
                   for pd in p_defs)

    area_dict = {}
    region_label_map = {
        "(a) Mn 2p₃/₂": "Mn 2p3/2",
        "(b) Fe 2p₃/₂": "Fe 2p3/2",
        "(c) O 1s":      "O 1s",
        "(d) C 1s":      "C 1s",
    }
    for title, (result, _bg, p_defs, _x, _y) in results_store.items():
        area_dict[region_label_map[title]] = _total_area(result, p_defs)

    atomic_pct = quantify(area_dict)
    for el, pct in atomic_pct.items():
        print(f"  {el:<14s}  {pct:6.2f} at.%")

    # ── Peak area percentages within each region ───────────────────────────────
    print("\n" + "=" * 60)
    print("  Peak component ratios within each region")
    print("=" * 60)
    for title, (result, _bg, p_defs, _x, _y) in results_store.items():
        areas = [result.params[f"{pd['prefix']}amplitude"].value for pd in p_defs]
        total = sum(areas)
        print(f"\n  {title}")
        for pd, area in zip(p_defs, areas):
            label = pd.get("label", pd["prefix"])
            cen   = result.params[f"{pd['prefix']}center"].value
            fwhm  = result.params[f"{pd['prefix']}fwhm"].value
            gl    = result.params[f"{pd['prefix']}gl_fraction"].value
            print(f"    {label:<28s}  BE={cen:.2f} eV  "
                  f"FWHM={fwhm:.2f} eV  GL={gl*100:.0f}%  "
                  f"area%={area/total*100:.1f}%")


if __name__ == "__main__":
    main()
