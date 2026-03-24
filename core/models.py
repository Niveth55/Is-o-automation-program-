"""
Data models for ISO Piping components.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PipeComponent:
    """Represents a single piping component (pipe, fitting, valve, flange)."""
    item_no: int
    tag_no: str
    comp_type: str           # PIPE, FITTING, VALVE, FLANGE, INSTRUMENT
    description: str
    size: str                # Nominal pipe size (e.g. "4", "6")
    size_2: Optional[str]    # Second size for reducers / reducing tees
    material: str            # Material code (e.g. CS, SS316)
    schedule: str            # Pipe schedule (e.g. SCH 40)
    pressure_class: str      # Rating class (e.g. 150#, 300#)
    quantity: float
    unit: str                # EA, M, SET
    weight_kg: float = 0.0
    end_connection: str = "BW"   # BW=Butt Weld, SW=Socket Weld, THD=Threaded, FF=Flat Face
    remarks: str = ""
    line_no: str = ""        # Pipeline / line number this component belongs to

    def to_dict(self) -> dict:
        return {
            "Item No.": self.item_no,
            "Tag No.": self.tag_no,
            "Description": self.description,
            "Size (inch)": self.size if not self.size_2 else f"{self.size} x {self.size_2}",
            "Material": self.material,
            "Schedule": self.schedule,
            "Pressure Class": self.pressure_class,
            "Quantity": self.quantity,
            "Unit": self.unit,
            "Weight (kg)": round(self.weight_kg, 2),
            "End Connection": self.end_connection,
            "Remarks": self.remarks,
        }


@dataclass
class PipeLine:
    """Represents a full piping line / spool."""
    line_no: str
    fluid: str
    fluid_service: str           # A, B, C, D
    design_pressure_bar: float
    design_temp_c: float
    operating_pressure_bar: float
    operating_temp_c: float
    pipe_spec: str               # Piping class / spec (e.g. A1A, B3B)
    insulation: bool = False
    insulation_type: str = ""
    heat_tracing: bool = False
    from_equip: str = ""
    to_equip: str = ""
    components: List[PipeComponent] = field(default_factory=list)

    @property
    def total_weight_kg(self) -> float:
        return sum(c.weight_kg for c in self.components)

    @property
    def component_count(self) -> int:
        return len(self.components)

    def add_component(self, component: PipeComponent):
        component.line_no = self.line_no
        self.components.append(component)

    def summary(self) -> dict:
        return {
            "Line No.": self.line_no,
            "Fluid": self.fluid,
            "Service Class": self.fluid_service,
            "Design P (bar)": self.design_pressure_bar,
            "Design T (°C)": self.design_temp_c,
            "Pipe Spec": self.pipe_spec,
            "Insulation": "Yes" if self.insulation else "No",
            "Heat Tracing": "Yes" if self.heat_tracing else "No",
            "From": self.from_equip,
            "To": self.to_equip,
            "Components": self.component_count,
            "Total Weight (kg)": round(self.total_weight_kg, 2),
        }


@dataclass
class IsoDrawing:
    """Represents an isometric drawing (spool / segment)."""
    drawing_no: str
    revision: str
    title: str
    line_no: str
    sheet: int
    total_sheets: int
    scale: str
    prepared_by: str
    checked_by: str
    approved_by: str
    date: str
    nodes: List[dict] = field(default_factory=list)   # coordinate nodes
    components: List[PipeComponent] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def add_note(self, note: str):
        self.notes.append(note)

    def title_block(self) -> dict:
        return {
            "Drawing No.": self.drawing_no,
            "Revision": self.revision,
            "Title": self.title,
            "Line No.": self.line_no,
            "Sheet": f"{self.sheet} of {self.total_sheets}",
            "Scale": self.scale,
            "Prepared By": self.prepared_by,
            "Checked By": self.checked_by,
            "Approved By": self.approved_by,
            "Date": self.date,
        }
