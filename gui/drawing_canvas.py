"""
Live drawing preview canvas — draws a simplified isometric pipe sketch
based on the current input values entered in the form.
"""
import tkinter as tk
import math
from gui.styles import BG_PREVIEW, FG_TITLE


class DrawingCanvas(tk.Canvas):
    """Tkinter canvas that renders a live isometric pipe preview."""

    LINE_COLOR   = "#40E0D0"
    DIM_COLOR    = "#AAFFFF"
    LABEL_COLOR  = "#FFFFFF"
    VALVE_COLOR  = "#FF9900"
    FLANGE_COLOR = "#88DDFF"

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=BG_PREVIEW,
            highlightthickness=0,
            **kwargs
        )
        self._pipe_data: dict = {}
        self.bind("<Configure>", lambda e: self.redraw())

    def update_data(self, data: dict):
        self._pipe_data = data
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        if not self._pipe_data:
            self._draw_placeholder(w, h)
            return

        self._draw_iso_pipe(w, h)

    # ------------------------------------------------------------------ #
    def _draw_placeholder(self, w, h):
        self.create_text(
            w // 2, h // 2 - 20,
            text="Pipe",
            fill=FG_TITLE,
            font=("Palatino Linotype", 32, "italic")
        )
        self.create_text(
            w // 2, h // 2 + 20,
            text="ISO View",
            fill="#555555",
            font=("Arial", 10)
        )

    # ------------------------------------------------------------------ #
    def _draw_iso_pipe(self, w, h):
        """Draw a simplified isometric representation of the piping spool."""
        d = self._pipe_data

        # Parse values with fallbacks
        def fval(key, default=50.0):
            try:
                return float(d.get(key) or default)
            except (ValueError, TypeError):
                return default

        size    = fval("size", 6)
        length  = fval("length", 10)
        angle   = fval("angle", 90)
        has_valve   = d.get("has_valve", False)
        has_flange  = d.get("has_flange", False)
        comp_type   = d.get("comp_type", "PIPE")

        # ── Scale to fit canvas ──────────────────────────────────────
        margin = 40
        pipe_w = max(4, min(size * 1.2, 20))   # visual pipe width px
        cw = w - 2 * margin
        ch = h - 2 * margin

        # ── Origin: bottom-left of canvas ────────────────────────────
        ox = margin + cw * 0.15
        oy = margin + ch * 0.75

        # ── Draw grid lines (iso grid) ────────────────────────────────
        self._draw_grid(w, h)

        if comp_type in ("PIPE", "FITTING"):
            self._draw_straight_run(ox, oy, cw, ch, pipe_w,
                                    length, angle, has_valve, has_flange, size)
        elif comp_type == "ELBOW":
            self._draw_elbow(ox, oy, cw, ch, pipe_w, angle, size)
        elif comp_type == "REDUCER":
            size2 = fval("size2", size * 0.6)
            self._draw_reducer(ox, oy, cw, ch, pipe_w, size, size2)
        else:
            self._draw_straight_run(ox, oy, cw, ch, pipe_w,
                                    length, angle, has_valve, has_flange, size)

        # ── Draw annotations ─────────────────────────────────────────
        self._draw_annotations(d, w, h)

    # ------------------------------------------------------------------ #
    def _draw_grid(self, w, h):
        """Faint isometric grid lines."""
        step = 30
        color = "#1A3333"
        # Horizontal
        for y in range(0, h, step):
            self.create_line(0, y, w, y, fill=color, dash=(2, 6))
        # 30-degree diagonals
        for x in range(-h, w, step):
            x2 = x + h * math.cos(math.radians(30)) * 2
            y2 = h * math.sin(math.radians(30)) * 2
            self.create_line(x, 0, x2, y2, fill=color, dash=(2, 6))

    # ------------------------------------------------------------------ #
    def _draw_straight_run(self, ox, oy, cw, ch, pw,
                            length, angle, has_valve, has_flange, size):
        """Draw a straight pipe run with optional valve and flange."""
        scale = min(cw, ch) / (length + 4)
        seg   = length * scale

        # ISO direction vectors (30° projection for X-axis)
        rad = math.radians(30)
        dx  = math.cos(rad) * seg
        dy  = -math.sin(rad) * seg   # y increases downward in tk

        ex, ey = ox + dx, oy + dy

        # Pipe body (double-line)
        offset = pw / 2
        perp_x = math.sin(rad) * offset
        perp_y = math.cos(rad) * offset

        self.create_line(ox - perp_x, oy - perp_y,
                         ex - perp_x, ey - perp_y,
                         fill=self.LINE_COLOR, width=2)
        self.create_line(ox + perp_x, oy + perp_y,
                         ex + perp_x, ey + perp_y,
                         fill=self.LINE_COLOR, width=2)
        # End caps
        self.create_line(ox - perp_x, oy - perp_y,
                         ox + perp_x, oy + perp_y,
                         fill=self.LINE_COLOR, width=2)
        self.create_line(ex - perp_x, ey - perp_y,
                         ex + perp_x, ey + perp_y,
                         fill=self.LINE_COLOR, width=2)

        # Valve symbol (diamond) at mid-point
        if has_valve:
            mx, my = (ox + ex) / 2, (oy + ey) / 2
            vs = pw * 2
            self.create_polygon(
                mx, my - vs, mx + vs, my, mx, my + vs, mx - vs, my,
                fill=self.VALVE_COLOR, outline=self.LINE_COLOR, width=1
            )
            self.create_text(mx, my - vs - 8,
                             text="V", fill=self.VALVE_COLOR,
                             font=("Arial", 7, "bold"))

        # Flange symbols at ends
        if has_flange:
            for px, py in [(ox, oy), (ex, ey)]:
                fw = pw * 1.8
                self.create_rectangle(
                    px - fw / 2, py - fw / 4,
                    px + fw / 2, py + fw / 4,
                    fill=self.FLANGE_COLOR, outline=self.LINE_COLOR
                )

        # Flow arrow
        ax, ay = (ox + ex) / 2 + perp_x + 6, (oy + ey) / 2 + perp_y + 6
        self.create_text(ax, ay, text="→", fill=self.DIM_COLOR,
                         font=("Arial", 10, "bold"))

        # Dimension line
        doff = pw + 12
        self.create_line(ox - perp_x - doff, oy - perp_y - doff,
                         ex - perp_x - doff, ey - perp_y - doff,
                         fill=self.DIM_COLOR, dash=(4, 3))
        mx2 = (ox + ex) / 2 - perp_x - doff - 4
        my2 = (oy + ey) / 2 - perp_y - doff - 4
        self.create_text(mx2, my2,
                         text=f"L={length:.1f}m",
                         fill=self.DIM_COLOR, font=("Arial", 8))

    # ------------------------------------------------------------------ #
    def _draw_elbow(self, ox, oy, cw, ch, pw, angle, size):
        """Draw a pipe elbow (arc)."""
        r  = min(cw, ch) * 0.3
        cx = ox + r
        cy = oy

        self.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=180, extent=-(180 - angle),
            style=tk.ARC,
            outline=self.LINE_COLOR, width=max(2, pw / 2)
        )
        # Inner arc
        ri = r - pw
        if ri > 5:
            self.create_arc(
                cx - ri, cy - ri, cx + ri, cy + ri,
                start=180, extent=-(180 - angle),
                style=tk.ARC,
                outline=self.LINE_COLOR, width=1
            )

        # Annotation
        self.create_text(cx, cy - r - 15,
                         text=f"{angle:.0f}° Elbow  NPS {size}\"",
                         fill=self.LABEL_COLOR, font=("Arial", 9))

    # ------------------------------------------------------------------ #
    def _draw_reducer(self, ox, oy, cw, ch, pw, size1, size2):
        """Draw a concentric reducer."""
        length = min(cw * 0.5, 120)
        w1 = max(4, min(size1 * 1.5, 25))
        w2 = max(3, min(size2 * 1.5, 18))

        ex = ox + length

        # Top line (tapered)
        self.create_line(ox, oy - w1, ex, ey := oy - w2,
                         fill=self.LINE_COLOR, width=2)
        # Bottom line
        self.create_line(ox, oy + w1, ex, oy + w2,
                         fill=self.LINE_COLOR, width=2)
        # End caps
        self.create_line(ox, oy - w1, ox, oy + w1,
                         fill=self.LINE_COLOR, width=2)
        self.create_line(ex, oy - w2, ex, oy + w2,
                         fill=self.LINE_COLOR, width=2)

        # Labels
        self.create_text(ox - 10, oy,
                         text=f'{size1}"', fill=self.DIM_COLOR,
                         font=("Arial", 8), anchor="e")
        self.create_text(ex + 10, oy,
                         text=f'{size2}"', fill=self.DIM_COLOR,
                         font=("Arial", 8), anchor="w")

    # ------------------------------------------------------------------ #
    def _draw_annotations(self, d, w, h):
        """Draw title block and key data at bottom of canvas."""
        line_no  = d.get("line_no", "")
        material = d.get("material", "")
        schedule = d.get("schedule", "")
        pclass   = d.get("pressure_class", "")
        spec     = d.get("pipe_spec", "")

        info = f"{line_no}  |  {material} {schedule}  |  {pclass}  |  Spec: {spec}"
        self.create_text(w // 2, h - 12,
                         text=info, fill="#888888",
                         font=("Courier New", 8))
