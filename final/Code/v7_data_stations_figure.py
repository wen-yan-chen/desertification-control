"""Section 3 station figure: stations on a real satellite basemap + observed cover.

Basemap: Esri World Imagery tiles (Web Mercator), downloaded and cached in
Data/v7/raw/basemap_tiles. Output: Paper/Figure/data_stations.{pdf,png}.
"""
import io, math, os, urllib.request
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "Data/v7/raw/basemap_tiles")
OUT = os.path.join(ROOT, "Paper/Figure/data_stations")
TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

SITES = [("YT", 36.85, 81.67, "I"), ("MF", 37.06, 82.68, "I"), ("QM", 38.13, 85.53, "I"),
         ("RQ", 39.02, 88.17, "I"), ("KEL", 41.76, 86.15, "I"), ("YL", 41.34, 86.26, "I"),
         ("ALE", 40.55, 81.28, "I"), ("XT", 38.83, 84.02, "II"), ("TZ", 38.97, 83.65, "III")]
COL = {"I": "#2b6cb0", "II": "#dd6b20", "III": "#718096"}
LAB = {"I": "Margin (calibration)", "II": "Corridor (context)", "III": "Interior (control)"}
OFF = {"YT": (6, -12), "MF": (7, -3), "QM": (6, 5), "RQ": (-8, 8), "KEL": (7, 4),
       "YL": (7, -10), "ALE": (7, 4), "XT": (7, -9), "TZ": (-20, 6)}
LON0, LON1, LAT0, LAT1 = 79.0, 89.6, 35.6, 42.6
Z = 7


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def tile_xy(lon, lat, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - merc_y(lat) / math.pi) / 2 * n


def get_tile(z, x, y):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"{z}_{x}_{y}.jpg")
    if not os.path.exists(p):
        req = urllib.request.Request(TILE_URL.format(z=z, x=x, y=y), headers={"User-Agent": "research-figure"})
        with urllib.request.urlopen(req, timeout=60) as r, open(p, "wb") as f:
            f.write(r.read())
    return Image.open(p).convert("RGB")


def basemap():
    fx0, fy0 = tile_xy(LON0, LAT1, Z)
    fx1, fy1 = tile_xy(LON1, LAT0, Z)
    x0, y0, x1, y1 = int(fx0), int(fy0), int(fx1), int(fy1)
    img = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            img.paste(get_tile(Z, x, y), ((x - x0) * 256, (y - y0) * 256))
    crop = img.crop((int((fx0 - x0) * 256), int((fy0 - y0) * 256),
                     int((fx1 - x0) * 256), int((fy1 - y0) * 256)))
    return np.asarray(crop)


def cover_stats():
    df = pd.read_csv(os.path.join(ROOT, "Data/v7/m1_audited/panel_m1.csv"), parse_dates=["date"])
    g = df[df.date.dt.month.between(6, 9)].dropna(subset=["V_pct"])
    yr = g.groupby(["site", g.date.dt.year]).V_pct.mean()
    return yr.groupby(level=0).agg(["mean", "std"])


def main():
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 10,
                         "mathtext.fontset": "stix"})
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"width_ratios": [1.25, 1]})

    # (a) satellite map, plotted in Mercator y so the image is undistorted
    y0, y1 = merc_y(LAT0), merc_y(LAT1)
    a.imshow(basemap(), extent=[LON0, LON1, y0, y1], interpolation="bilinear")
    a.set_xlim(LON0, LON1); a.set_ylim(y0, y1)
    a.set_aspect(180 / math.pi)  # equal scale: 1 rad Mercator y = 57.3 deg lon
    halo = [pe.withStroke(linewidth=2.6, foreground="white")]
    for code, lat, lon, cat in SITES:
        a.scatter(lon, merc_y(lat), s=60, c=COL[cat], edgecolor="white", lw=1.2, zorder=3)
        a.annotate(code, (lon, merc_y(lat)), xytext=OFF[code], textcoords="offset points",
                   color=COL[cat], weight="bold", fontsize=10, path_effects=halo, zorder=4)
    a.text(84.3, merc_y(39.9), "Taklamakan Desert", ha="center", color="white", style="italic",
           fontsize=11, path_effects=[pe.withStroke(linewidth=2, foreground="#5a4630")])
    lats = np.arange(36, 43, 2)
    a.set_yticks([merc_y(v) for v in lats]); a.set_yticklabels([f"{v}°N" for v in lats])
    a.set_xticks(range(80, 90, 2)); a.set_xticklabels([f"{v}°E" for v in range(80, 90, 2)])
    for code, c in LAB.items():
        a.scatter([], [], c=COL[code], edgecolor="white", s=45, label=c)
    a.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
    a.set_title("(a) Stations", loc="left", weight="bold")
    a.text(0.01, 0.01, "Basemap: Esri World Imagery", transform=a.transAxes, fontsize=6.5,
           color="white", path_effects=[pe.withStroke(linewidth=1.5, foreground="black")])

    # (b) observed cover
    st = cover_stats()
    order = [s[0] for s in SITES]
    cats = {s[0]: s[3] for s in SITES}
    yy = np.arange(len(order))[::-1]
    m, sd = st.loc[order, "mean"].values, st.loc[order, "std"].values
    b.barh(yy, m, xerr=sd, color=[COL[cats[c]] for c in order], height=0.75,
           error_kw=dict(ecolor="#333", lw=0.9, capsize=3))
    for y, v, e in zip(yy, m, sd):
        b.text(v + e + 0.8, y, f"{v:.1f}", va="center", fontsize=9)
    b.set_yticks(yy); b.set_yticklabels(order)
    b.set_xlim(0, 50); b.set_xlabel("Mean growing-season $V$ (%)")
    b.grid(axis="x", ls=":", lw=0.5, alpha=0.6)
    b.set_title("(b) Observed cover, 2015–2025", loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(OUT + ".pdf"); fig.savefig(OUT + ".png", dpi=250)


if __name__ == "__main__":
    main()
