"""
ISO Drawing Generator — produces AutoCAD script files (.scr) and
human-readable isometric drawing data for each piping line/spool.

The .scr files can be drag-and-dropped into AutoCAD to automatically
draw the isometric representation of the piping spool.
"""
import os
import math
from typing import List, Tuple, Optional
from datetime import date

from core.models import PipeLine, PipeComponent, IsoDrawing
from config.settings import SCRIPTS_DIR, DRAWINGS_DIR, ISO_DRAW_SETTINGS


# Isometric axis unit vectors (30° projection)
# X-axis → right,  Y-axis → up,  Z-axis → left-forward
ISO_X = (math.cos(math.radians(30)),  math.sin(math.radians(30)))
ISO_Y = (0.0, 1.0)
ISO_Z = (-math.cos(math.radians(30)), math.sin(math.radians(30)))

SYMBOL_SCALE = {
    "EL90": 1.0,
    "EL45": 0.8,
    "TEE": 1.0,
    "RED": 1.2,
    "ERED": 1.2,
    "FLG": 0.5,
    "VALVE": 2.0,
    "CAP": 0.4,
}


def _iso_point(x: float, y: float, z: float, scale: float = 50.0) -> Tuple[float, float]:
    """Convert 3D iso coords to 2D drawing coords."""
    dx = (x - z) * scale * ISO_X[0]
    dy = (x * ISO_X[1] + y * ISO_Y[1] + z * ISO_Z[1]) * scale
    return dx, dy


class ISODrawingGenerator:
    """Generates AutoCAD script files and isometric drawing reports."""

    def __init__(self, project_name: str = "Project",
                 scripts_dir: str = SCRIPTS_DIR,
                 drawings_dir: str = DRAWINGS_DIR):
        self.project_name = project_name
        self.scripts_dir = scripts_dir
        self.drawings_dir = drawings_dir
        os.makedirs(self.scripts_dir, exist_ok=True)
        os.makedirs(self.drawings_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Generate AutoCAD script (.scr) for a piping line
    # ------------------------------------------------------------------ #
    def generate_autocad_script(self, line: PipeLine,
                                  drawing_no: str = "",
                                  filename: Optional[str] = None) -> str:
        if not drawing_no:
            drawing_no = f"ISO-{line.line_no.replace('/', '-')}-001"
        safe = line.line_no.replace("/", "-").replace(" ", "_")
        if filename is None:
            filename = f"{safe}_ISO.scr"
        path = os.path.join(self.scripts_dir, filename)

        lines_scr = []
        lines_scr.append("; ============================================================")
        lines_scr.append(f"; AutoCAD Script — ISO Piping Drawing")
        lines_scr.append(f"; Project  : {self.project_name}")
        lines_scr.append(f"; Line No. : {line.line_no}")
        lines_scr.append(f"; Drawing  : {drawing_no}")
        lines_scr.append(f"; Generated: {date.today()}")
        lines_scr.append("; ============================================================")
        lines_scr.append("")

        # Set up layers
        lines_scr += [
            "; --- Layer Setup ---",
            "LAYER NEW ISO-PIPE",
            "LAYER COLOR 7 ISO-PIPE",
            "LAYER NEW ISO-FITTING",
            "LAYER COLOR 3 ISO-FITTING",
            "LAYER NEW ISO-VALVE",
            "LAYER COLOR 1 ISO-VALVE",
            "LAYER NEW ISO-ANNOTATION",
            "LAYER COLOR 2 ISO-ANNOTATION",
            "LAYER NEW ISO-TITLE",
            "LAYER COLOR 5 ISO-TITLE",
            "",
        ]

        # Draw pipe runs (simple isometric representation)
        x, y, z = 0.0, 0.0, 0.0
        pipe_length_m = 0.0
        directions = [
            (1, 0, 0),   # +X  right
            (0, 1, 0),   # +Y  up
            (-1, 0, 0),  # -X  left
            (0, 0, 1),   # +Z  forward
        ]
        dir_idx = 0

        for comp in line.components:
            if comp.comp_type == "PIPE":
                length = comp.quantity  # metres
                pipe_length_m += length
                dx, dy, dz = directions[dir_idx % len(directions)]
                nx, ny, nz = x + dx * length, y + dy * length, z + dz * length

                p1 = _iso_point(x, y, z)
                p2 = _iso_point(nx, ny, nz)

                lines_scr.append(f"; Pipe segment — {comp.size}\" {comp.schedule} L={length}m")
                lines_scr.append("LAYER SET ISO-PIPE")
                lines_scr.append(f"LINE {p1[0]:.3f},{p1[1]:.3f} {p2[0]:.3f},{p2[1]:.3f} ")
                # Second line offset for pipe width
                ow = max(1.5, float(comp.size.replace("-", ".").split("/")[0]) * 0.3
                         if "/" in comp.size else float(comp.size) * 0.3)
                lines_scr.append(f"LINE {p1[0]+ow:.3f},{p1[1]:.3f} {p2[0]+ow:.3f},{p2[1]:.3f} ")
                lines_scr.append("")

                # Pipe annotation
                mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                lines_scr.append("LAYER SET ISO-ANNOTATION")
                lines_scr.append(
                    f"TEXT {mid[0]:.3f},{mid[1]+2:.3f} 2.5 0 "
                    f"{comp.size}\" {comp.schedule}"
                )
                lines_scr.append(
                    f"TEXT {mid[0]:.3f},{mid[1]-2:.3f} 2.0 0 L={length}m"
                )
                lines_scr.append("")

                x, y, z = nx, ny, nz
                dir_idx += 1

            elif comp.comp_type in ("FITTING", "FLANGE"):
                sym_scale = SYMBOL_SCALE.get(comp.tag_no[:3].upper(), 1.0)
                p = _iso_point(x, y, z)
                lines_scr.append(f"; Fitting — {comp.description} {comp.size}\"")
                lines_scr.append("LAYER SET ISO-FITTING")
                lines_scr.append(
                    f"INSERT {comp.tag_no[:3].upper()} {p[0]:.3f},{p[1]:.3f} "
                    f"{sym_scale} {sym_scale} 0"
                )
                lines_scr.append("")

            elif comp.comp_type == "VALVE":
                p = _iso_point(x, y, z)
                lines_scr.append(f"; Valve — {comp.description} {comp.size}\"")
                lines_scr.append("LAYER SET ISO-VALVE")
                lines_scr.append(
                    f"INSERT VALVE_{comp.tag_no[:3].upper()} {p[0]:.3f},{p[1]:.3f} "
                    f"2.0 2.0 0"
                )
                lines_scr.append(
                    f"TEXT {p[0]+3:.3f},{p[1]+2:.3f} 2.0 0 {comp.tag_no}"
                )
                lines_scr.append("")

        # Title block
        lines_scr += self._title_block_script(line, drawing_no)

        with open(path, "w") as f:
            f.write("\n".join(lines_scr))
            f.write("\n")

        return path

    def _title_block_script(self, line: PipeLine, drawing_no: str) -> List[str]:
        s = [
            "; --- Title Block ---",
            "LAYER SET ISO-TITLE",
            "RECTANGLE -20,-30 280,10",
            f"TEXT 0,-5 3.0 0 DRAWING NO.: {drawing_no}",
            f"TEXT 0,-10 3.0 0 LINE NO.: {line.line_no}",
            f"TEXT 0,-15 3.0 0 FLUID: {line.fluid}   SPEC: {line.pipe_spec}",
            f"TEXT 0,-20 3.0 0 DESIGN: {line.design_pressure_bar} bar / {line.design_temp_c} degC",
            f"TEXT 0,-25 2.5 0 DATE: {date.today()}",
            "",
        ]
        return s

    # ------------------------------------------------------------------ #
    # Human-readable isometric data report
    # ------------------------------------------------------------------ #
    def generate_iso_report(self, line: PipeLine,
                             drawing_no: str = "",
                             filename: Optional[str] = None) -> str:
        if not drawing_no:
            drawing_no = f"ISO-{line.line_no.replace('/', '-')}-001"
        safe = line.line_no.replace("/", "-").replace(" ", "_")
        if filename is None:
            filename = f"{safe}_ISO_Report.txt"
        path = os.path.join(self.drawings_dir, filename)

        with open(path, "w") as f:
            f.write("=" * 70 + "\n")
            f.write(f"  ISOMETRIC DRAWING DATA REPORT\n")
            f.write(f"  Drawing No. : {drawing_no}\n")
            f.write(f"  Project     : {self.project_name}\n")
            f.write(f"  Line No.    : {line.line_no}\n")
            f.write(f"  Fluid       : {line.fluid}\n")
            f.write(f"  Pipe Spec   : {line.pipe_spec}\n")
            f.write(
                f"  Design      : {line.design_pressure_bar} bar g  /  "
                f"{line.design_temp_c} °C\n"
            )
            f.write(
                f"  Operating   : {line.operating_pressure_bar} bar g  /  "
                f"{line.operating_temp_c} °C\n"
            )
            insul = f"{line.insulation_type}" if line.insulation else "None"
            f.write(f"  Insulation  : {insul}\n")
            ht = "Yes" if line.heat_tracing else "No"
            f.write(f"  Heat Tracing: {ht}\n")
            f.write(f"  From        : {line.from_equip}\n")
            f.write(f"  To          : {line.to_equip}\n")
            f.write("=" * 70 + "\n\n")

            f.write(
                f"{'No.':<5} {'Tag':<15} {'Type':<12} {'Description':<30} "
                f"{'Size':<10} {'Qty':>6} {'Unit':<5} {'Wt(kg)':>8}\n"
            )
            f.write("-" * 95 + "\n")
            total_wt = 0.0
            for comp in line.components:
                sz = comp.size if not comp.size_2 else f"{comp.size}x{comp.size_2}"
                f.write(
                    f"{comp.item_no:<5} {comp.tag_no:<15} {comp.comp_type:<12} "
                    f"{comp.description:<30} {sz:<10} "
                    f"{comp.quantity:>6.1f} {comp.unit:<5} {comp.weight_kg:>8.2f}\n"
                )
                total_wt += comp.weight_kg
            f.write("-" * 95 + "\n")
            f.write(
                f"{'TOTAL':<5} {'':<15} {'':<12} {'':<30} {'':<10} "
                f"{'':>6} {'':<5} {round(total_wt,2):>8.2f}\n"
            )

        return path

    # ------------------------------------------------------------------ #
    # Batch generate for all lines
    # ------------------------------------------------------------------ #
    def generate_all(self, lines: List[PipeLine]) -> dict:
        results = {"scripts": [], "reports": []}
        for i, line in enumerate(lines, start=1):
            dwg_no = f"ISO-{line.line_no.replace('/', '-')}-{i:03d}"
            scr_path = self.generate_autocad_script(line, dwg_no)
            rpt_path = self.generate_iso_report(line, dwg_no)
            results["scripts"].append(scr_path)
            results["reports"].append(rpt_path)
        return results
