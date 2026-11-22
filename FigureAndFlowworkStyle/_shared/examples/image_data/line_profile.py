"""Plot grayscale intensity along a line on a real image; pixel coordinates start at top left."""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps

from mcm_style import head, panels, paper_context, save_paper


def line_profile(image, start, end, *, credit):
    """Return the annotated figure and the exact distance/intensity series drawn."""
    if not credit.strip():
        raise ValueError("Supply the image source")
    image = ImageOps.exif_transpose(image).convert("RGB")
    points = np.asarray([start, end], dtype=float)
    if (points.shape != (2, 2) or not np.isfinite(points).all() or (points < 0).any()
            or (points > np.asarray(image.size) - 1).any()):
        raise ValueError("Endpoints must be inside the displayed image")
    length = np.linalg.norm(points[1] - points[0])
    if not length:
        raise ValueError("The line needs two distinct endpoints")
    coords = np.linspace(points[0], points[1], int(np.ceil(length)) + 1)
    px, py = np.rint(coords).astype(int).T
    values = np.asarray(image.convert("L"))[py, px]
    distance = np.linspace(0, length, len(values))
    fig, axes = panels(3.25, 1, 2)
    photo, profile = axes[0]
    photo.imshow(image)
    photo.plot(*points.T, color="white", linewidth=3)
    photo.plot(*points.T, color="#A12D22", linewidth=1.2, marker="o", markersize=4)
    for label, xy in zip("AB", points):
        photo.annotate(label, xy, xytext=(0, 5), textcoords="offset points", ha="center",
                       bbox=dict(facecolor="white", edgecolor="none", pad=1))
    photo.set(xticks=[], yticks=[], xlabel=credit)
    head(photo, "a", "Image and sampling line")
    profile.plot(distance, values, color="#285987", linewidth=1.2)
    profile.set(xlabel="Distance from A (pixels)", ylabel="Grayscale intensity (0–255)",
                ylim=(0, 255), xlim=(0, length))
    head(profile, "b", "Intensity along A–B")
    return fig, np.column_stack([distance, values])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("out", type=Path, help="Output stem")
    parser.add_argument("--line", nargs=4, type=float, required=True, metavar=("X1", "Y1", "X2", "Y2"))
    parser.add_argument("--credit", required=True)
    args = parser.parse_args()
    with Image.open(args.image) as image, paper_context():
        fig, series = line_profile(image, args.line[:2], args.line[2:], credit=args.credit)
        csv_path = args.out.with_suffix(".csv")
        if csv_path.exists():
            raise FileExistsError(csv_path)
        paths, issues = save_paper(fig, args.out)
        np.savetxt(csv_path, series, delimiter=",", header="distance_px,grayscale", comments="",
                   fmt=("%.5f", "%d"))
        print(paths["png"], [(issue.code, issue.detail) for issue in issues])
        plt.close(fig)
