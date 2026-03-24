"""
Global configuration settings for ISO Piping Automation.
"""

# Supported pipe schedule standards
PIPE_SCHEDULES = ["SCH 10", "SCH 20", "SCH 30", "SCH 40", "SCH 80", "SCH 160", "XXS", "XS", "STD"]

# Pipe material grades
PIPE_MATERIALS = {
    "CS": "Carbon Steel",
    "SS304": "Stainless Steel 304",
    "SS316": "Stainless Steel 316",
    "LTCS": "Low Temperature Carbon Steel",
    "DSS": "Duplex Stainless Steel",
    "INCOLOY": "Incoloy 825",
    "INCONEL": "Inconel 625",
}

# Standard nominal pipe sizes (inches)
NOMINAL_PIPE_SIZES = [
    "1/4", "3/8", "1/2", "3/4",
    "1", "1-1/4", "1-1/2", "2", "2-1/2",
    "3", "3-1/2", "4", "5", "6", "8", "10", "12",
    "14", "16", "18", "20", "24", "28", "30", "36"
]

# Pressure rating classes
PRESSURE_CLASSES = ["150#", "300#", "600#", "900#", "1500#", "2500#"]

# Fluid service categories
FLUID_SERVICES = {
    "A": "Highly toxic / flammable above auto-ignition temp",
    "B": "Flammable, toxic, or damaging to human tissue",
    "C": "Not in category A or B",
    "D": "Non-flammable, non-toxic, not damaging",
}

# Default output directories
OUTPUT_DIR = "output"
REPORTS_DIR = "output/reports"
DRAWINGS_DIR = "output/drawings"
SCRIPTS_DIR = "output/autocad_scripts"

# BOM column definitions
BOM_COLUMNS = [
    "Item No.", "Tag No.", "Description", "Size (inch)",
    "Material", "Schedule", "Pressure Class",
    "Quantity", "Unit", "Weight (kg)", "Remarks"
]

# Isometric drawing default settings
ISO_DRAW_SETTINGS = {
    "paper_size": "A1",
    "scale": "1:50",
    "north_arrow": True,
    "revision_block": True,
    "title_block": True,
    "line_weight": 0.35,
    "text_height": 2.5,
}
