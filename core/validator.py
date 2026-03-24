"""
ISO Piping Validator — checks piping lines and components against
ASME B31.3 Process Piping rules and project piping specifications.
"""
import json
import os
from typing import List, Tuple

from core.models import PipeLine, PipeComponent
from config.settings import (
    NOMINAL_PIPE_SIZES, PIPE_SCHEDULES, PIPE_MATERIALS,
    PRESSURE_CLASSES, FLUID_SERVICES
)


SPECS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "pipe_specs.json")


def _load_specs() -> dict:
    with open(SPECS_PATH) as f:
        return json.load(f)


class PipingValidator:
    """Validates piping lines and components for compliance."""

    def __init__(self):
        self.specs = _load_specs()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _reset(self):
        self.errors = []
        self.warnings = []

    # ------------------------------------------------------------------ #
    # Component-level validation
    # ------------------------------------------------------------------ #
    def validate_component(self, comp: PipeComponent) -> Tuple[bool, List[str], List[str]]:
        self._reset()

        # 1. Nominal pipe size
        if comp.size not in self.specs["pipe_od_mm"]:
            self.errors.append(
                f"[{comp.tag_no}] Unknown nominal size '{comp.size}'. "
                f"Supported: {list(self.specs['pipe_od_mm'].keys())}"
            )

        # 2. Schedule
        if comp.schedule not in PIPE_SCHEDULES:
            self.errors.append(
                f"[{comp.tag_no}] Unknown schedule '{comp.schedule}'. "
                f"Supported: {PIPE_SCHEDULES}"
            )

        # 3. Material
        if comp.material not in PIPE_MATERIALS:
            self.warnings.append(
                f"[{comp.tag_no}] Material '{comp.material}' not in standard list. "
                f"Verify specification."
            )

        # 4. Pressure class
        if comp.pressure_class not in PRESSURE_CLASSES:
            self.errors.append(
                f"[{comp.tag_no}] Invalid pressure class '{comp.pressure_class}'. "
                f"Supported: {PRESSURE_CLASSES}"
            )

        # 5. Quantity
        if comp.quantity <= 0:
            self.errors.append(
                f"[{comp.tag_no}] Quantity must be greater than zero. Got: {comp.quantity}"
            )

        ok = len(self.errors) == 0
        return ok, list(self.errors), list(self.warnings)

    # ------------------------------------------------------------------ #
    # Line-level validation (ASME B31.3 basic checks)
    # ------------------------------------------------------------------ #
    def validate_line(self, line: PipeLine) -> Tuple[bool, List[str], List[str]]:
        self._reset()

        # Fluid service
        if line.fluid_service not in FLUID_SERVICES:
            self.errors.append(
                f"[{line.line_no}] Invalid fluid service '{line.fluid_service}'. "
                f"Must be one of {list(FLUID_SERVICES.keys())}."
            )

        # Design pressure must be positive
        if line.design_pressure_bar <= 0:
            self.errors.append(
                f"[{line.line_no}] Design pressure must be > 0 bar. Got: {line.design_pressure_bar}"
            )

        # Design temp sanity
        if line.design_temp_c < -200 or line.design_temp_c > 1000:
            self.warnings.append(
                f"[{line.line_no}] Design temperature {line.design_temp_c}°C is outside "
                f"typical range (-200 to 1000°C). Verify."
            )

        # Operating conditions must not exceed design
        if line.operating_pressure_bar > line.design_pressure_bar:
            self.errors.append(
                f"[{line.line_no}] Operating pressure ({line.operating_pressure_bar} bar) "
                f"exceeds design pressure ({line.design_pressure_bar} bar)."
            )

        if line.operating_temp_c > line.design_temp_c:
            self.errors.append(
                f"[{line.line_no}] Operating temperature ({line.operating_temp_c}°C) "
                f"exceeds design temperature ({line.design_temp_c}°C)."
            )

        # At least one component
        if not line.components:
            self.warnings.append(
                f"[{line.line_no}] No components defined for this line."
            )

        # Validate each component
        for comp in line.components:
            ok, errs, warns = self.validate_component(comp)
            self.errors.extend(errs)
            self.warnings.extend(warns)

        # Fluid service A & B must have specific inspection note
        if line.fluid_service in ("A", "B"):
            self.warnings.append(
                f"[{line.line_no}] Category {line.fluid_service} fluid — "
                f"ensure 100% radiography and hydro-test per ASME B31.3 Table 341.3.2."
            )

        ok = len(self.errors) == 0
        return ok, list(self.errors), list(self.warnings)

    # ------------------------------------------------------------------ #
    # Batch validation of all lines
    # ------------------------------------------------------------------ #
    def validate_project(self, lines: List[PipeLine]) -> dict:
        results = {}
        total_errors = 0
        total_warnings = 0

        for line in lines:
            ok, errs, warns = self.validate_line(line)
            results[line.line_no] = {
                "passed": ok,
                "errors": errs,
                "warnings": warns,
            }
            total_errors += len(errs)
            total_warnings += len(warns)

        return {
            "lines_checked": len(lines),
            "lines_passed": sum(1 for r in results.values() if r["passed"]),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "details": results,
        }
