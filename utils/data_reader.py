"""
Data reader utilities — load piping project data from JSON, CSV, or Excel.
"""
import json
import csv
import os
from typing import List, Optional


def read_json(path: str) -> dict:
    """Read project data from a JSON file."""
    with open(path) as f:
        return json.load(f)


def read_csv_line_list(path: str) -> dict:
    """
    Read a piping line list from a CSV file and convert it into
    the standard project data format expected by ISOPipingProcessor.

    Expected CSV columns:
    line_no, fluid, fluid_service, design_pressure_bar, design_temp_c,
    operating_pressure_bar, operating_temp_c, pipe_spec, insulation,
    heat_tracing, from_equip, to_equip
    """
    lines_data = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            line_info = {
                "line_no": row.get("line_no", ""),
                "fluid": row.get("fluid", ""),
                "fluid_service": row.get("fluid_service", "C"),
                "design_pressure_bar": float(row.get("design_pressure_bar", 0) or 0),
                "design_temp_c": float(row.get("design_temp_c", 0) or 0),
                "operating_pressure_bar": float(row.get("operating_pressure_bar", 0) or 0),
                "operating_temp_c": float(row.get("operating_temp_c", 0) or 0),
                "pipe_spec": row.get("pipe_spec", ""),
                "insulation": row.get("insulation", "").strip().lower() in ("yes", "true", "1"),
                "insulation_type": row.get("insulation_type", ""),
                "heat_tracing": row.get("heat_tracing", "").strip().lower() in ("yes", "true", "1"),
                "from_equip": row.get("from_equip", ""),
                "to_equip": row.get("to_equip", ""),
            }
            lines_data.append({"line_info": line_info, "components": []})

    return {"lines": lines_data}


def read_csv_components(path: str) -> List[dict]:
    """
    Read piping components from a CSV file.

    Expected CSV columns:
    line_no, tag_no, comp_type, description, size, size_2, material,
    schedule, pressure_class, quantity, unit, end_connection, remarks
    """
    components: dict = {}  # keyed by line_no
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            line_no = row.get("line_no", "")
            if line_no not in components:
                components[line_no] = []
            components[line_no].append({
                "tag_no": row.get("tag_no", ""),
                "comp_type": row.get("comp_type", "FITTING"),
                "description": row.get("description", ""),
                "size": row.get("size", ""),
                "size_2": row.get("size_2") or None,
                "material": row.get("material", "CS"),
                "schedule": row.get("schedule", "SCH 40"),
                "pressure_class": row.get("pressure_class", "150#"),
                "quantity": float(row.get("quantity", 1) or 1),
                "unit": row.get("unit", "EA"),
                "end_connection": row.get("end_connection", "BW"),
                "remarks": row.get("remarks", ""),
            })
    return components


def merge_csv_data(lines_path: str, components_path: str) -> dict:
    """Merge line list CSV and components CSV into a unified project dict."""
    project = read_csv_line_list(lines_path)
    components_map = read_csv_components(components_path)

    for line_entry in project["lines"]:
        line_no = line_entry["line_info"]["line_no"]
        line_entry["components"] = components_map.get(line_no, [])

    return project
