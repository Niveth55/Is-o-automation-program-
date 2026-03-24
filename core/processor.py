"""
ISO Piping Processor — reads line list data, builds PipeLine objects,
calculates pipe lengths, weights, and prepares data for downstream modules.
"""
import json
import os
import math
from typing import List, Optional

from core.models import PipeLine, PipeComponent

SPECS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "pipe_specs.json")


def _load_specs() -> dict:
    with open(SPECS_PATH) as f:
        return json.load(f)


class ISOPipingProcessor:
    """Core processing engine for ISO piping automation."""

    def __init__(self):
        self.specs = _load_specs()
        self.lines: List[PipeLine] = []

    # ------------------------------------------------------------------ #
    # Weight calculation helpers
    # ------------------------------------------------------------------ #
    def get_od_mm(self, size: str) -> float:
        return self.specs["pipe_od_mm"].get(size, 0.0)

    def get_wt_mm(self, size: str, schedule: str) -> float:
        sched_data = self.specs["wall_thickness_mm"].get(schedule, {})
        return sched_data.get(size, 0.0)

    def calc_pipe_weight_per_m(self, size: str, schedule: str,
                               density_kg_m3: float = 7850.0) -> float:
        """Calculate pipe weight in kg/m using OD and wall thickness."""
        od = self.get_od_mm(size) / 1000.0   # m
        wt = self.get_wt_mm(size, schedule) / 1000.0  # m
        if od == 0 or wt == 0:
            return 0.0
        id_ = od - 2 * wt
        area = math.pi / 4.0 * (od**2 - id_**2)
        return area * density_kg_m3

    def calc_component_weight(self, comp: PipeComponent) -> float:
        """Estimate component weight based on type and size."""
        if comp.comp_type == "PIPE":
            w_per_m = self.calc_pipe_weight_per_m(comp.size, comp.schedule)
            return w_per_m * comp.quantity   # quantity in metres for pipe
        # Fitting / valve weights — simplified factor-based estimate
        od = self.get_od_mm(comp.size)
        base_weight = (od / 100.0) ** 2 * 2.0   # rough kg estimate
        multipliers = {
            "FITTING": 1.0,
            "FLANGE": 2.0,
            "VALVE": 4.0,
            "INSTRUMENT": 1.5,
        }
        m = multipliers.get(comp.comp_type, 1.0)
        return base_weight * m * comp.quantity

    # ------------------------------------------------------------------ #
    # Build a PipeLine from raw dict data (e.g. from CSV/Excel row)
    # ------------------------------------------------------------------ #
    def build_line(self, line_data: dict) -> PipeLine:
        """
        Build a PipeLine from a dictionary.
        Expected keys: line_no, fluid, fluid_service, design_pressure_bar,
        design_temp_c, operating_pressure_bar, operating_temp_c, pipe_spec,
        insulation (bool), heat_tracing (bool), from_equip, to_equip
        """
        line = PipeLine(
            line_no=str(line_data.get("line_no", "UNKNOWN")),
            fluid=str(line_data.get("fluid", "")),
            fluid_service=str(line_data.get("fluid_service", "C")),
            design_pressure_bar=float(line_data.get("design_pressure_bar", 0)),
            design_temp_c=float(line_data.get("design_temp_c", 0)),
            operating_pressure_bar=float(line_data.get("operating_pressure_bar", 0)),
            operating_temp_c=float(line_data.get("operating_temp_c", 0)),
            pipe_spec=str(line_data.get("pipe_spec", "")),
            insulation=bool(line_data.get("insulation", False)),
            insulation_type=str(line_data.get("insulation_type", "")),
            heat_tracing=bool(line_data.get("heat_tracing", False)),
            from_equip=str(line_data.get("from_equip", "")),
            to_equip=str(line_data.get("to_equip", "")),
        )
        return line

    # ------------------------------------------------------------------ #
    # Build a PipeComponent from raw dict data
    # ------------------------------------------------------------------ #
    def build_component(self, item_no: int, comp_data: dict) -> PipeComponent:
        comp = PipeComponent(
            item_no=item_no,
            tag_no=str(comp_data.get("tag_no", f"ITEM-{item_no:03d}")),
            comp_type=str(comp_data.get("comp_type", "FITTING")).upper(),
            description=str(comp_data.get("description", "")),
            size=str(comp_data.get("size", "")),
            size_2=comp_data.get("size_2"),
            material=str(comp_data.get("material", "CS")),
            schedule=str(comp_data.get("schedule", "SCH 40")),
            pressure_class=str(comp_data.get("pressure_class", "150#")),
            quantity=float(comp_data.get("quantity", 1)),
            unit=str(comp_data.get("unit", "EA")),
            end_connection=str(comp_data.get("end_connection", "BW")),
            remarks=str(comp_data.get("remarks", "")),
        )
        comp.weight_kg = self.calc_component_weight(comp)
        return comp

    # ------------------------------------------------------------------ #
    # Process full project data
    # ------------------------------------------------------------------ #
    def process(self, project_data: dict) -> List[PipeLine]:
        """
        Process full project data.
        project_data structure:
        {
          "lines": [
            {
              "line_info": { ... },
              "components": [ { ... }, ... ]
            },
            ...
          ]
        }
        """
        self.lines = []
        for line_entry in project_data.get("lines", []):
            line = self.build_line(line_entry.get("line_info", {}))
            for i, comp_data in enumerate(line_entry.get("components", []), start=1):
                comp = self.build_component(i, comp_data)
                line.add_component(comp)
            self.lines.append(line)
        return self.lines

    def summary(self) -> dict:
        total_weight = sum(l.total_weight_kg for l in self.lines)
        total_components = sum(l.component_count for l in self.lines)
        return {
            "total_lines": len(self.lines),
            "total_components": total_components,
            "total_weight_kg": round(total_weight, 2),
            "lines": [l.summary() for l in self.lines],
        }
