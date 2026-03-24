# ISO Piping Automation Program

An automation system for **ISO (Isometric) piping design** that processes piping line data and auto-generates:

- **Bill of Materials (BOM)** — CSV and Excel formats
- **AutoCAD Isometric Scripts** (`.scr`) — drag-and-drop into AutoCAD
- **Isometric Drawing Data Reports** — per-line text reports
- **ASME B31.3 Validation** — design pressure, temperature, fluid service checks

---

## Features

| Feature | Description |
|---|---|
| Pipe data processing | Reads line lists and component data from JSON or CSV |
| Weight calculation | Auto-calculates pipe/fitting/valve weights using OD and wall thickness |
| ASME B31.3 validation | Checks design conditions, fluid service categories, pressure ratings |
| BOM generation | Consolidated + per-line BOMs in CSV and Excel |
| AutoCAD `.scr` generation | Ready-to-run isometric drawing scripts |
| ISO drawing reports | Human-readable spool data sheets |

---

## Project Structure

```
Is-o-automation-program-/
├── main.py                    # CLI entry point
├── requirements.txt
├── config/
│   ├── settings.py            # Material grades, pressure classes, schedules
│   └── pipe_specs.json        # OD, wall thickness, weight tables
├── core/
│   ├── models.py              # PipeComponent, PipeLine, IsoDrawing dataclasses
│   ├── processor.py           # Process raw data → PipeLine objects + weight calc
│   ├── validator.py           # ASME B31.3 compliance checks
│   ├── bom_generator.py       # BOM CSV / Excel export
│   └── iso_generator.py       # AutoCAD .scr + ISO drawing report generator
├── utils/
│   └── data_reader.py         # JSON / CSV input readers
├── data/
│   ├── sample_project.py      # Built-in demo data (3 piping lines)
│   ├── sample_line_list.csv   # Sample CSV line list
│   └── sample_components.csv  # Sample CSV component list
├── tests/
│   └── test_pipeline.py       # 17 unit tests (pytest)
└── output/                    # Generated files (created at runtime)
    ├── reports/               # BOM + summary reports
    ├── drawings/              # ISO drawing data reports
    └── autocad_scripts/       # AutoCAD .scr files
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run demo

```bash
python main.py --demo
```

### 3. Run with your own data

**JSON input:**
```bash
python main.py --input data/my_project.json --project-name MyPlant
```

**CSV input (line list + components):**
```bash
python main.py --lines data/line_list.csv --components data/components.csv --project-name MyPlant
```

**Validate only:**
```bash
python main.py --input data/my_project.json --validate-only
```

**BOM only:**
```bash
python main.py --input data/my_project.json --bom-only
```

---

## Input Format

### JSON format (`--input`)

```json
{
  "lines": [
    {
      "line_info": {
        "line_no": "6\"-PW-1001-A1A",
        "fluid": "Process Water",
        "fluid_service": "C",
        "design_pressure_bar": 10.0,
        "design_temp_c": 80.0,
        "operating_pressure_bar": 7.5,
        "operating_temp_c": 60.0,
        "pipe_spec": "A1A",
        "insulation": false,
        "heat_tracing": false,
        "from_equip": "T-101",
        "to_equip": "P-101A"
      },
      "components": [
        {
          "tag_no": "PIPE-1001-01",
          "comp_type": "PIPE",
          "description": "Seamless Pipe",
          "size": "6",
          "material": "CS",
          "schedule": "SCH 40",
          "pressure_class": "150#",
          "quantity": 12.5,
          "unit": "M",
          "end_connection": "BW"
        }
      ]
    }
  ]
}
```

### CSV format (two files: `--lines` + `--components`)

**line_list.csv** columns:
`line_no, fluid, fluid_service, design_pressure_bar, design_temp_c, operating_pressure_bar, operating_temp_c, pipe_spec, insulation, insulation_type, heat_tracing, from_equip, to_equip`

**components.csv** columns:
`line_no, tag_no, comp_type, description, size, size_2, material, schedule, pressure_class, quantity, unit, end_connection, remarks`

---

## Supported Standards

| Standard | Application |
|---|---|
| ASME B31.3 | Process piping design validation |
| ASME B36.10 | Carbon steel pipe dimensions |
| ASME B36.19M | Stainless steel pipe dimensions |
| ASME B16.9 | Factory-made butt-weld fittings |
| ASME B16.5 | Pipe flanges and flanged fittings |
| ASME B16.11 | Forged socket-weld fittings |
| ASME B16.34 | Valves |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

All 17 tests cover processor, validator, and model logic.
