"""Offline Web Mercator maps for the station/route pattern in Paper2026 02."""

from dataclasses import dataclass
from pathlib import Path

import matplotlib.patheffects as pe
import numpy as np
from PIL import Image, ImageEnhance

from mcm_style import palette as P

LIMIT = 85.0511287798
EARTH_RADIUS_KM = 6371.0088


def mercator(latitude):
    latitude = np.asarray(latitude, dtype=float)
    if not np.isfinite(latitude).all() or (np.abs(latitude) > LIMIT).any():
        raise ValueError("Latitude is outside Web Mercator")
    return np.degrees(np.arcsinh(np.tan(np.radians(latitude))))


def cached_tiles(tile_dir, extent, *, zoom, pattern="{z}_{x}_{y}.jpg", saturation=.72):
    """Read local XYZ tiles for (west, east, south, north); never fetch tiles."""
    west, east, south, north = extent
    if not (-180 <= west < east <= 180 and -LIMIT <= south < north <= LIMIT
            and isinstance(zoom, int) and 0 <= zoom <= 22
            and np.isfinite(saturation) and saturation >= 0):
        raise ValueError("Invalid zoom, extent (no dateline crossing), or saturation")
    n = 2**zoom
    x0, x1 = (np.array([west, east])+180)/360*n
    y0, y1 = (180-mercator([north, south]))/360*n
    a, c = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
    b, d = min(n, int(np.ceil(x1))), min(n, int(np.ceil(y1)))
    if (b-a)*(d-c) > 256:
        raise ValueError("Requested mosaic exceeds 256 tiles; narrow the extent or lower zoom")
    mosaic = Image.new("RGB", ((b-a)*256, (d-c)*256))
    for i in range(a, b):
        for j in range(c, d):
            path = Path(tile_dir) / pattern.format(z=zoom, x=i, y=j)
            with Image.open(path) as tile:
                if tile.size != (256, 256):
                    raise ValueError(f"Expected a 256×256 XYZ tile: {path}")
                mosaic.paste(tile.convert("RGB"), ((i-a)*256, (j-c)*256))
    crop = tuple(round((v-origin)*256) for v, origin in zip((x0, y0, x1, y1), (a,c,a,c)))
    if crop[0] >= crop[2] or crop[1] >= crop[3]:
        raise ValueError("Extent is smaller than one pixel at this zoom")
    return ImageEnhance.Color(mosaic.crop(crop)).enhance(saturation)


@dataclass(frozen=True)
class Site:
    label: str
    longitude: float
    latitude: float
    category: str
    offset: tuple = (5, 5)  # points


def study_map(ax, extent, sites, *, image=None, attribution=None, styles, route=None,
              route_label="Study route", scale=None, longitude_ticks=(), latitude_ticks=()):
    """Draw sites and a route in lon/lat, with a north arrow and local scale.

    styles maps categories to (color, marker). scale is (lon, lat, distance_km)
    for the left end of a horizontal bar; the distance applies at that latitude.
    image must be a Web Mercator raster cropped to extent; attribute its source.
    """
    west, east, south, north = extent
    if not (-180 <= west < east <= 180 and -LIMIT <= south < north <= LIMIT):
        raise ValueError("Use an ordered longitude/latitude extent with no dateline crossing")
    bottom, top = mercator([south, north])
    fg = "white" if image is not None else P.INK
    stroke = [pe.withStroke(linewidth=2.4, foreground=P.INK)] if image is not None else []
    if image is not None:
        if not attribution:
            raise ValueError("Attribute the raster source")
        ax.imshow(image, extent=(west, east, bottom, top), interpolation="bilinear", origin="upper")
    if route is not None:
        route = np.asarray(route, dtype=float)
        if (route.ndim != 2 or route.shape[1] != 2 or len(route) < 2
                or not np.isfinite(route).all() or (np.abs(route[:,0]) > 180).any()):
            raise ValueError("Route needs at least two longitude/latitude pairs")
        ax.plot(route[:,0], mercator(route[:,1]), color=P.AMBER if image is None else "#FFE391",
                ls="--", lw=1.8, zorder=3, path_effects=stroke, label=route_label)
    shown = set()
    for site in sites:
        if not (west <= site.longitude <= east and south <= site.latitude <= north):
            raise ValueError(f"Site outside map extent: {site.label}")
        xy = (site.longitude, mercator(site.latitude))
        color, marker = styles[site.category]
        ax.scatter(*xy, c=color, marker=marker, s=46, edgecolor="white", linewidth=.9,
                   zorder=4, label=None if site.category in shown else site.category)
        ax.annotate(site.label, xy, site.offset, textcoords="offset points", color=fg,
                    fontsize=8.5, weight="bold", path_effects=stroke, zorder=5)
        shown.add(site.category)
    if scale is not None:
        lon, lat, km = scale
        ratio = np.sin(km/(2*EARTH_RADIUS_KM))/np.cos(np.radians(lat))
        if not (west <= lon < east and south < lat < north and 0 < km <= np.pi*EARTH_RADIUS_KM
                and 0 < ratio <= 1):
            raise ValueError("Scale needs a valid position and distance")
        end = lon + np.degrees(2*np.arcsin(ratio))
        if end > east:
            raise ValueError("Scale bar runs outside the map")
        y = mercator(lat)
        ax.plot([lon, end], [y, y], color=fg, lw=1.9, path_effects=stroke, zorder=6)
        ax.annotate(f"{km:g} km", ((lon+end)/2, y), (0, 3), textcoords="offset points",
                    ha="center", color=fg, path_effects=stroke, zorder=6)
    ax.text(.94, .95, "N", transform=ax.transAxes, ha="center", va="top", color=fg,
            weight="bold", path_effects=stroke)
    ax.annotate("", (.94, .865), (.94, .77), xycoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "color": fg, "lw": 1.1})
    if attribution:
        ax.text(.017, .037, attribution, transform=ax.transAxes, fontsize=8.1,
                color=fg, path_effects=stroke)
    def degrees(n, positive, negative):
        return f"{abs(n):g}°{positive if n >= 0 else negative}"
    xt, yt = tuple(longitude_ticks), tuple(latitude_ticks)
    ax.set(aspect="equal", xticks=xt, xticklabels=[degrees(v, "E", "W") for v in xt],
           yticks=mercator(yt), yticklabels=[degrees(v, "N", "S") for v in yt],
           xlim=(west, east), ylim=(bottom, top))
    ax.grid(True, color=fg, alpha=.25, linewidth=.5)
    return ax
