"""Trace every green contour so the draw matches the original logo."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes, label

SRC = Path(
    r"C:\Users\MatKa\.cursor\projects\c-Users-MatKa-spacexhackathon"
    r"\assets\c__Users_MatKa_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_995bbadcf03dddc5c8f5813be0e766fa_images_Bear_Logo-7614558c-fdf1-4ec1-9ca9-9e03d77b675c.png"
)
OUT = Path(__file__).parent / "bear.svg"
COLOR = "#037e52"

NEIGH = (
    (-1, 0), (-1, 1), (0, 1), (1, 1),
    (1, 0), (1, -1), (0, -1), (-1, -1),
)


def rdp(points, eps):
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    dx, dy = end[0] - start[0], end[1] - start[1]
    denom = (dx * dx + dy * dy) ** 0.5 or 1.0
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        p = points[i]
        dist = abs(dy * p[0] - dx * p[1] + end[0] * start[1] - end[1] * start[0]) / denom
        if dist > dmax:
            dmax, idx = dist, i
    if dmax > eps:
        left = rdp(points[: idx + 1], eps)
        right = rdp(points[idx:], eps)
        return left[:-1] + right
    return [start, end]


def trace(mask):
    h, w = mask.shape
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return []
    y0 = int(ys.min())
    x0 = int(xs[ys == y0].min())
    start = (y0, x0)
    back = 0
    for i, (dy, dx) in enumerate(NEIGH):
        ny, nx = start[0] + dy, start[1] + dx
        if not (0 <= ny < h and 0 <= nx < w) or not mask[ny, nx]:
            back = i
            break
    path = [start]
    y, x = start
    b = back
    for _ in range(int(mask.sum()) * 4 + 8):
        hit = None
        for k in range(8):
            i = (b + k) % 8
            ny, nx = y + NEIGH[i][0], x + NEIGH[i][1]
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx]:
                hit = (ny, nx)
                b = (i + 5) % 8
                break
        if hit is None or hit == start:
            break
        path.append(hit)
        y, x = hit
    return path


def d_attr(pts, pad, scale, eps):
    pts = rdp(pts, eps)
    if len(pts) < 4:
        return ""
    parts = []
    for i, (y, x) in enumerate(pts):
        cmd = "M" if i == 0 else "L"
        parts.append(f"{cmd}{x * scale + pad:.1f},{y * scale + pad:.1f}")
    parts.append("Z")
    return " ".join(parts)


def contours_for(blob, pad, scale, eps):
    filled = binary_fill_holes(blob)
    loops = []
    d = d_attr(trace(filled), pad, scale, eps)
    if d:
        loops.append(d)
    interior = filled & ~blob
    hole_labels, n_holes = label(interior)
    for i in range(1, n_holes + 1):
        hole = hole_labels == i
        if hole.sum() < 25:
            continue
        d = d_attr(trace(hole), pad, scale, eps)
        if d:
            loops.append(d)
    return loops


def main():
    im = Image.open(SRC).convert("RGBA")
    scale = 520 / im.width
    im = im.resize((520, int(round(im.height * scale))), Image.Resampling.LANCZOS)
    arr = np.array(im)
    g, r, b, a = arr[:, :, 1], arr[:, :, 0], arr[:, :, 2], arr[:, :, 3]
    green = (g > 70) & (a > 60) & (g > r + 15) & (g > b)

    labeled, n = label(green)
    sizes = [(i, (labeled == i).sum()) for i in range(1, n + 1)]
    sizes.sort(key=lambda t: -t[1])
    print("components", sizes)

    pad = 16
    h, w = green.shape
    vw, vh = w + pad * 2, h + pad * 2

    line_ds = []
    fill_ds = []
    for i, area in sizes:
        blob = labeled == i
        eps = 0.75 if area > 5000 else 0.55
        loops = contours_for(blob, pad, 1.0, eps)
        line_ds.extend(loops)
        fill_ds.append(" ".join(loops))
        print("cc", i, "area", area, "loops", len(loops))

    lines_xml = []
    for i, d in enumerate(line_ds):
        lines_xml.append(
            f'  <path class="bear-line" pathLength="1" fill="none" '
            f'stroke="{COLOR}" stroke-width="2.2" stroke-linejoin="round" '
            f'stroke-linecap="round" d="{d}"/>'
        )

    fill_d = " ".join(fill_ds)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}" aria-hidden="true">
  <path class="bear-fill" fill-rule="evenodd" fill="{COLOR}" stroke="none" d="{fill_d}"/>
{chr(10).join(lines_xml)}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print("wrote", OUT, "lines", len(line_ds), "viewBox", vw, vh)


if __name__ == "__main__":
    main()
