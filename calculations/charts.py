"""Tiny pure-Python SVG chart helpers (line / scatter) with axes + grid.

No external deps — produces inline SVG strings suitable for embedding
into the result panel.
"""
from __future__ import annotations
import math


_COLORS = ["#0F2C4A", "#B0203A", "#6FB1D8", "#234A78", "#3F7A4A", "#A8742C"]


def _nice_step(span, target_ticks=5):
    if span <= 0:
        return 1.0
    raw = span / max(target_ticks, 1)
    p = 10 ** math.floor(math.log10(raw))
    n = raw / p
    if n < 1.5:
        nice = 1
    elif n < 3:
        nice = 2
    elif n < 7:
        nice = 5
    else:
        nice = 10
    return nice * p


def _fmt(v):
    if v == 0:
        return "0"
    av = abs(v)
    if av < 0.01 or av >= 1e5:
        return f"{v:.2e}"
    if av < 1:
        return f"{v:.3f}"
    if av < 100:
        return f"{v:.2f}"
    return f"{v:.0f}"


def line_chart(title, xlabel, ylabel, series, width=520, height=320,
               y_min=None, y_max=None, x_min=None, x_max=None,
               show_legend=True, show_points=False):
    """Return SVG string for a line chart.

    series: list of dicts: {'name': str, 'points': [(x,y), ...],
                            'color': '#hex' (optional),
                            'dashed': bool (optional),
                            'marker': bool (optional)}
    """
    pad_l, pad_r, pad_t, pad_b = 60, 20, 36, 50
    plot_w = width  - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    # Collect bounds
    xs_all, ys_all = [], []
    for s in series:
        for x, y in s.get("points", []):
            if x is None or y is None or not math.isfinite(x) or not math.isfinite(y):
                continue
            xs_all.append(x)
            ys_all.append(y)
    if not xs_all:
        return f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg"></svg>'
    x0 = x_min if x_min is not None else min(xs_all)
    x1 = x_max if x_max is not None else max(xs_all)
    y0 = y_min if y_min is not None else min(ys_all)
    y1 = y_max if y_max is not None else max(ys_all)
    if x1 == x0:
        x1 = x0 + 1.0
    if y1 == y0:
        y1 = y0 + 1.0

    # Add 5% padding to y range
    y_pad = (y1 - y0) * 0.05
    y0 -= y_pad
    y1 += y_pad

    def sx(v):
        return pad_l + (v - x0) / (x1 - x0) * plot_w

    def sy(v):
        return pad_t + plot_h - (v - y0) / (y1 - y0) * plot_h

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="chart">'
    )
    parts.append(
        '<style>'
        '.chart-ttl{font:bold 12px "Segoe UI",sans-serif;fill:#0F2C4A}'
        '.chart-axis{font:10px "Segoe UI",sans-serif;fill:#234A78}'
        '.chart-grid{stroke:#DCE3EB;stroke-width:0.7}'
        '.chart-axline{stroke:#234A78;stroke-width:1}'
        '.chart-legend{font:10px "Segoe UI",sans-serif;fill:#234A78}'
        '</style>'
    )
    # Title
    parts.append(
        f'<text x="{width/2}" y="18" class="chart-ttl" text-anchor="middle">{title}</text>'
    )

    # Gridlines + ticks (X)
    x_step = _nice_step(x1 - x0, 6)
    x_t = math.ceil(x0 / x_step) * x_step
    while x_t <= x1 + 1e-9:
        gx = sx(x_t)
        parts.append(f'<line x1="{gx:.1f}" y1="{pad_t}" x2="{gx:.1f}" y2="{pad_t+plot_h}" class="chart-grid"/>')
        parts.append(
            f'<text x="{gx:.1f}" y="{pad_t+plot_h+14}" class="chart-axis" '
            f'text-anchor="middle">{_fmt(x_t)}</text>'
        )
        x_t += x_step

    y_step = _nice_step(y1 - y0, 6)
    y_t = math.ceil(y0 / y_step) * y_step
    while y_t <= y1 + 1e-9:
        gy = sy(y_t)
        parts.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{pad_l+plot_w}" y2="{gy:.1f}" class="chart-grid"/>')
        parts.append(
            f'<text x="{pad_l-6}" y="{gy+3:.1f}" class="chart-axis" '
            f'text-anchor="end">{_fmt(y_t)}</text>'
        )
        y_t += y_step

    # Axes
    parts.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t+plot_h}" class="chart-axline"/>')
    parts.append(f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{pad_l+plot_w}" y2="{pad_t+plot_h}" class="chart-axline"/>')

    # Axis labels
    parts.append(
        f'<text x="{pad_l+plot_w/2}" y="{height-12}" class="chart-axis" '
        f'text-anchor="middle">{xlabel}</text>'
    )
    parts.append(
        f'<text transform="translate(16 {pad_t+plot_h/2}) rotate(-90)" '
        f'class="chart-axis" text-anchor="middle">{ylabel}</text>'
    )

    # Series
    for i, s in enumerate(series):
        color = s.get("color") or _COLORS[i % len(_COLORS)]
        dash  = ' stroke-dasharray="5 4"' if s.get("dashed") else ''
        pts = [(sx(x), sy(y)) for x, y in s.get("points", [])
               if x is not None and y is not None and math.isfinite(x) and math.isfinite(y)]
        if len(pts) >= 2:
            d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            parts.append(
                f'<path d="{d}" stroke="{color}" stroke-width="1.8" fill="none"{dash}/>'
            )
        if s.get("marker") or show_points:
            for x, y in pts:
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}"/>'
                )

    # Legend
    if show_legend and len(series) > 1:
        lx = pad_l + 8
        ly = pad_t + 6
        for i, s in enumerate(series):
            color = s.get("color") or _COLORS[i % len(_COLORS)]
            parts.append(
                f'<line x1="{lx}" y1="{ly}" x2="{lx+18}" y2="{ly}" '
                f'stroke="{color}" stroke-width="2"/>'
            )
            parts.append(
                f'<text x="{lx+22}" y="{ly+3}" class="chart-legend">{s.get("name","")}</text>'
            )
            ly += 14

    parts.append("</svg>")
    return "".join(parts)


def step_polyline(points, color="#B0203A"):
    """Return SVG path commands for a step (rectangular) polyline – used for
    McCabe–Thiele stepping. `points` is a list of (x, y) ordered along the
    stepping direction. Returns just <path> element."""
    if len(points) < 2:
        return ""
    d = ["M", f"{points[0][0]:.4f}", f"{points[0][1]:.4f}"]
    for i in range(1, len(points)):
        x, y = points[i]
        d += ["L", f"{x:.4f}", f"{y:.4f}"]
    return f'<path d="{" ".join(d)}" stroke="{color}" stroke-width="1.5" fill="none"/>'
