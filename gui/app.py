"""
ISO Piping Automation — Desktop GUI Application
================================================
Mimics the style of industrial duct/piping automation software (e.g. Duct v18).
Built with Python tkinter — no external GUI library required.

Layout
------
┌─────────────────────────────────────────────────────────────────────────┐
│  Title bar  "ISO Piping Automation  v1.0"                               │
│  Server Name: [_____________]   [Proceed]                               │
├──────────────────────────────────┬──────────────────────────────────────┤
│  Project Details                 │  Drawing Preview (live canvas)       │
│  ─ Project ID  ─ Client          │                                      │
│  ─ Element ID  ─ Consultant      │  [isometric pipe sketch]             │
│  ─ Line No.    ─ Dept / Group    │                                      │
├──────────────────────────────────┤                                      │
│  Material / Document ID          │                                      │
├──────────────────────────────────┤                                      │
│  Pipe Details                    │                                      │
│  ─ Size, Schedule, Mat, P-Class  │                                      │
│  ─ Length, Angle, Radius         │                                      │
│  ─ Pressure, Temp, Design Cond.  │                                      │
├──────────────────────────────────┴──────────────────────────────────────┤
│  Fabrication options  ─ Inlet/Outlet Flange  ─ Action buttons          │
│  Status bar                                                             │
└─────────────────────────────────────────────────────────────────────────┘
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.styles import *
from gui.drawing_canvas import DrawingCanvas
from core.processor import ISOPipingProcessor
from core.validator import PipingValidator
from core.bom_generator import BOMGenerator
from core.iso_generator import ISODrawingGenerator
from config.settings import (
    NOMINAL_PIPE_SIZES, PIPE_SCHEDULES, PIPE_MATERIALS,
    PRESSURE_CLASSES, FLUID_SERVICES
)


# ─────────────────────────────────────────────────────────────────────────────
class ISOPipingApp(tk.Tk):
    """Main application window."""

    VERSION = "v1.0"

    def __init__(self):
        super().__init__()
        self.title(f"ISO Piping Automation  {self.VERSION}")
        self.geometry("1280x860")
        self.minsize(1100, 780)
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)

        self._vars: dict = {}     # all StringVar / BooleanVar widgets
        self._build_ui()
        self._bind_preview_refresh()

    # ══════════════════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_menubar()
        self._build_header()
        self._build_body()
        self._build_footer()

    # ── Menu bar ──────────────────────────────────────────────────────────────
    def _build_menubar(self):
        menu = tk.Menu(self, bg=BG_DARK, fg=FG_LABEL,
                       activebackground=FG_BUTTON_BG,
                       activeforeground=FG_LABEL, tearoff=0)
        self.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0, bg=BG_DARK, fg=FG_LABEL,
                            activebackground=FG_BUTTON_BG)
        file_menu.add_command(label="New Project",  command=self._on_new)
        file_menu.add_command(label="Open JSON...", command=self._on_open_json)
        file_menu.add_command(label="Open CSV...",  command=self._on_open_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",         command=self.destroy)
        menu.add_cascade(label="File", menu=file_menu)

        run_menu = tk.Menu(menu, tearoff=0, bg=BG_DARK, fg=FG_LABEL,
                           activebackground=FG_BUTTON_BG)
        run_menu.add_command(label="Run Demo",      command=self._run_demo)
        run_menu.add_command(label="Validate",      command=self._run_validate)
        run_menu.add_command(label="Generate BOM",  command=self._run_bom)
        run_menu.add_command(label="Generate All",  command=self._run_all)
        menu.add_cascade(label="Run", menu=run_menu)

        menu.add_cascade(label="Help")

    # ── Header row ────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_DARK, height=40)
        hdr.pack(fill="x", padx=0, pady=0)

        tk.Label(hdr, text="ISO Piping Automation",
                 bg=BG_DARK, fg=FG_TITLE,
                 font=("Palatino Linotype", 14, "italic bold")
                 ).pack(side="left", padx=12, pady=6)

        tk.Label(hdr, text=self.VERSION,
                 bg=BG_DARK, fg="#888888", font=FONT_VERSION
                 ).pack(side="left", padx=0, pady=6)

        # Server name row
        srv_row = tk.Frame(self, bg=BG_MAIN)
        srv_row.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(srv_row, text="Server Name", bg=BG_MAIN,
                 fg=FG_LABEL, font=FONT_LABEL).pack(side="left", padx=(0, 6))
        self._vars["server"] = tk.StringVar(value="localhost")
        tk.Entry(srv_row, textvariable=self._vars["server"],
                 width=30, bg=BG_ENTRY, fg=FG_ENTRY,
                 font=FONT_ENTRY).pack(side="left", padx=4)
        self._btn("Proceed", srv_row, self._on_proceed, side="left", padx=8)

    # ── Main body (left panels + right canvas) ────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=6, pady=4)

        # Left column — all input panels
        left = tk.Frame(body, bg=BG_MAIN)
        left.pack(side="left", fill="both", expand=False)

        self._build_project_panel(left)
        self._build_matdoc_panel(left)
        self._build_pipe_details_panel(left)
        self._build_fabrication_panel(left)

        # Right column — drawing canvas
        right = tk.Frame(body, bg=BG_PANEL, relief=SECTION_RELIEF, bd=2)
        right.pack(side="right", fill="both", expand=True, padx=(6, 0))

        tk.Label(right, text="Pipe", bg=BG_PANEL, fg=FG_TITLE,
                 font=("Palatino Linotype", 22, "italic")
                 ).pack(pady=(8, 0))

        self.canvas = DrawingCanvas(right, width=400, height=480)
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

    # ── Project Details panel ─────────────────────────────────────────────────
    def _build_project_panel(self, parent):
        f = self._section(parent, "Project Details")

        row1 = tk.Frame(f, bg=BG_PANEL)
        row1.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(row1, "Project ID",  "project_id",  ENTRY_WIDTH)
        self._lbl_entry(row1, "Client",      "client",      ENTRY_WIDTH_LG)

        row2 = tk.Frame(f, bg=BG_PANEL)
        row2.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(row2, "Element ID",  "element_id",  ENTRY_WIDTH)
        self._lbl_entry(row2, "Consultant",  "consultant",  ENTRY_WIDTH_LG)

        row3 = tk.Frame(f, bg=BG_PANEL)
        row3.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(row3, "Line No.",    "line_no",     ENTRY_WIDTH)
        self._lbl_entry(row3, "I.W.T",       "iwt",         8)
        self._lbl_combo(row3, "Responsible Dept", "resp_dept",
                        ["MECHANICAL", "PIPING", "CIVIL", "ELECTRICAL"],
                        width=14)
        self._lbl_entry(row3, "Group Name",  "group_name",  10)

    # ── Material / Document ID panel ─────────────────────────────────────────
    def _build_matdoc_panel(self, parent):
        f = self._section(parent, "Mat. Std")

        # Header labels
        cols = ["Project ID", "Element ID", "Category", "Drg No",
                "Document Title", "Item Code", "Quantity", "Mat. Std"]
        hdr = tk.Frame(f, bg=BG_PANEL)
        hdr.pack(fill="x")
        for c in cols:
            tk.Label(hdr, text=c, bg=BG_PANEL, fg=FG_LABEL,
                     font=FONT_LABEL_SM, width=10, anchor="center"
                     ).pack(side="left", padx=1)

        # Entry row
        doc_row = tk.Frame(f, bg=BG_PANEL)
        doc_row.pack(fill="x", pady=2)
        tk.Label(doc_row, text="Document ID :", bg=BG_PANEL,
                 fg=FG_LABEL, font=FONT_LABEL).pack(side="left")
        keys = ["doc_proj_id", "doc_elem_id", "doc_category", "doc_drg_no",
                "doc_title", "doc_item_code", "doc_qty", "doc_mat_std"]
        widths = [8, 10, 8, 10, 14, 10, 5, 8]
        for k, w in zip(keys, widths):
            self._vars[k] = tk.StringVar()
            tk.Entry(doc_row, textvariable=self._vars[k],
                     width=w, bg=BG_ENTRY, fg=FG_ENTRY,
                     font=FONT_ENTRY).pack(side="left", padx=2)

    # ── Pipe Details panel ────────────────────────────────────────────────────
    def _build_pipe_details_panel(self, parent):
        f = self._section(parent, "Pipe / Spool Details")

        # Flange Option
        fo_row = tk.Frame(f, bg=BG_PANEL)
        fo_row.pack(fill="x", pady=PAD_Y)
        tk.Label(fo_row, text="Flange Option", bg=BG_PANEL,
                 fg=FG_LABEL, font=FONT_LABEL).pack(side="left", padx=(0, 6))
        self._vars["flange_option"] = tk.StringVar()
        tk.Entry(fo_row, textvariable=self._vars["flange_option"],
                 width=50, bg=BG_ENTRY, fg=FG_ENTRY,
                 font=FONT_ENTRY).pack(side="left")

        # With Hole checkbox
        self._vars["with_hole"] = tk.BooleanVar()
        tk.Checkbutton(f, text="With Hole",
                       variable=self._vars["with_hole"],
                       bg=CHECK_BG, fg=CHECK_FG,
                       selectcolor=BG_DARK,
                       activebackground=CHECK_BG,
                       font=FONT_LABEL).pack(anchor="w", padx=PAD_X)

        # ── Pipe size group ──
        size_frame = self._section(f, "Pipe Size / Dimensions (mm)")

        row_a = tk.Frame(size_frame, bg=BG_PANEL)
        row_a.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(row_a, "Inlet Arm Length (A)",    "inlet_arm",    8)
        self._lbl_entry(row_a, "Outlet Arm Length (B)",   "outlet_arm",   8)

        row_b = tk.Frame(size_frame, bg=BG_PANEL)
        row_b.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(row_b, "Inlet Opening Breadth (C)",  "inlet_breadth",  8)
        self._lbl_entry(row_b, "Outlet Opening Breadth (D)", "outlet_breadth", 8)

        row_c = tk.Frame(size_frame, bg=BG_PANEL)
        row_c.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(row_c, "Pipe Height (E)",          "pipe_height",  8)
        self._lbl_entry(row_c, "Pipe Angle (G) °",         "pipe_angle",   8)

        row_d = tk.Frame(size_frame, bg=BG_PANEL)
        row_d.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(row_d, "Inner Radius (R1)",        "inner_radius", 8)

        # ── Pipe spec row ──
        spec_row = tk.Frame(f, bg=BG_PANEL)
        spec_row.pack(fill="x", pady=PAD_Y)
        self._lbl_combo(spec_row, "NPS (inch)", "size",
                        NOMINAL_PIPE_SIZES, width=7)
        self._lbl_combo(spec_row, "Schedule",   "schedule",
                        PIPE_SCHEDULES, width=10)
        self._lbl_combo(spec_row, "Material",   "material",
                        list(PIPE_MATERIALS.keys()), width=10)
        self._lbl_combo(spec_row, "Pres. Class","pressure_class",
                        PRESSURE_CLASSES, width=8)

        spec_row2 = tk.Frame(f, bg=BG_PANEL)
        spec_row2.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(spec_row2, "Pipe Spec",   "pipe_spec",     8)
        self._lbl_entry(spec_row2, "Plate Thk (mm)", "plate_thk",  6)
        self._lbl_entry(spec_row2, "Mat Spec",    "mat_spec",      10)
        self._lbl_combo(spec_row2, "Comp. Type",  "comp_type",
                        ["PIPE", "FITTING", "ELBOW", "REDUCER",
                         "VALVE", "FLANGE"], width=10)

        cond_row = tk.Frame(f, bg=BG_PANEL)
        cond_row.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(cond_row, "Pressure (bar)",  "design_pressure", 7)
        self._lbl_entry(cond_row, "Temp (°C)",        "design_temp",     7)
        self._lbl_entry(cond_row, "LRB Thk (mm)",     "lrb_thk",         6)
        self._lbl_combo(cond_row, "Fluid Service",    "fluid_service",
                        list(FLUID_SERVICES.keys()), width=5)

        quant_row = tk.Frame(f, bg=BG_PANEL)
        quant_row.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(quant_row, "Quantity",    "quantity",  7)
        self._lbl_combo(quant_row, "Unit",        "unit",
                        ["M", "EA", "SET", "KG"], width=6)
        self._lbl_entry(quant_row, "Tag No.",     "tag_no",    14)

    # ── Fabrication panel ─────────────────────────────────────────────────────
    def _build_fabrication_panel(self, parent):
        f = self._section(parent, "Fabrication & Flanges")

        fab_row = tk.Frame(f, bg=BG_PANEL)
        fab_row.pack(fill="x", pady=PAD_Y)
        fab_options = ["Separate Plate", "Single Unit",
                       "Tapping", "Branches", "Man Hole"]
        for opt in fab_options:
            key = opt.lower().replace(" ", "_")
            self._vars[key] = tk.BooleanVar()
            tk.Checkbutton(fab_row, text=opt,
                           variable=self._vars[key],
                           bg=CHECK_BG, fg=CHECK_FG,
                           selectcolor=BG_DARK,
                           activebackground=CHECK_BG,
                           font=FONT_LABEL
                           ).pack(side="left", padx=6)

        flange_row = tk.Frame(f, bg=BG_PANEL)
        flange_row.pack(fill="x", pady=PAD_Y)

        # Inlet Flange
        in_flg = self._section(flange_row, "Inlet Flange", relief="ridge")
        in_flg.pack(side="left", padx=(0, 10), fill="y")
        self._vars["inlet_flange"] = tk.StringVar(value="Standard")
        for val in ("Standard", "User Input"):
            tk.Radiobutton(in_flg, text=val,
                           variable=self._vars["inlet_flange"],
                           value=val,
                           bg=RADIO_BG, fg=RADIO_FG,
                           selectcolor=BG_DARK,
                           activebackground=RADIO_BG,
                           font=FONT_LABEL).pack(anchor="w")

        # Outlet Flange
        out_flg = self._section(flange_row, "Outlet Flange", relief="ridge")
        out_flg.pack(side="left", padx=(0, 10), fill="y")
        self._vars["outlet_flange"] = tk.StringVar(value="Standard")
        for val in ("Standard", "User Input"):
            tk.Radiobutton(out_flg, text=val,
                           variable=self._vars["outlet_flange"],
                           value=val,
                           bg=RADIO_BG, fg=RADIO_FG,
                           selectcolor=BG_DARK,
                           activebackground=RADIO_BG,
                           font=FONT_LABEL).pack(anchor="w")

        extra_row = tk.Frame(f, bg=BG_PANEL)
        extra_row.pack(fill="x", pady=PAD_Y)
        self._lbl_entry(extra_row, "Corner Angle Required",  "corner_angle",  6)
        self._lbl_entry(extra_row, "Baffle Plate Required",  "baffle_plate",  6)

        # ── Action buttons ──
        btn_row = tk.Frame(f, bg=BG_PANEL)
        btn_row.pack(fill="x", pady=(8, 2))
        self._btn("Validate",     btn_row, self._run_validate, side="left", padx=4)
        self._btn("Generate BOM", btn_row, self._run_bom,      side="left", padx=4)
        self._btn("ISO Script",   btn_row, self._run_iso,      side="left", padx=4)
        self._btn("Run All",      btn_row, self._run_all,
                  side="left", padx=4, bg="#007A7A")
        self._btn("Clear",        btn_row, self._on_new,
                  side="right", padx=4, bg="#AA4444")

    # ── Footer / status bar ───────────────────────────────────────────────────
    def _build_footer(self):
        self.status_var = tk.StringVar(value="Ready.")
        bar = tk.Frame(self, bg=BG_DARK, height=22)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self.status_var,
                 bg=BG_DARK, fg="#AAFFAA",
                 font=FONT_STATUS, anchor="w"
                 ).pack(side="left", padx=8)
        tk.Label(bar,
                 text=f"ISO Piping Automation {self.VERSION}  |  "
                      f"ASME B31.3  |  {date.today()}",
                 bg=BG_DARK, fg="#666666",
                 font=FONT_VERSION, anchor="e"
                 ).pack(side="right", padx=8)

    # ══════════════════════════════════════════════════════════════════════════
    # Helper widget builders
    # ══════════════════════════════════════════════════════════════════════════

    def _section(self, parent, title: str, relief="groove") -> tk.LabelFrame:
        f = tk.LabelFrame(
            parent, text=f" {title} ",
            bg=BG_PANEL, fg=FG_LABEL,
            font=FONT_SECTION,
            relief=relief, bd=1,
            labelanchor="nw"
        )
        f.pack(fill="x", padx=SECTION_PAD, pady=SECTION_PAD)
        return f

    def _lbl_entry(self, parent, label: str, key: str, width: int):
        tk.Label(parent, text=label, bg=BG_PANEL,
                 fg=FG_LABEL, font=FONT_LABEL
                 ).pack(side="left", padx=(PAD_X, 2))
        self._vars[key] = tk.StringVar()
        e = tk.Entry(parent, textvariable=self._vars[key],
                     width=width, bg=BG_ENTRY, fg=FG_ENTRY,
                     font=FONT_ENTRY)
        e.pack(side="left", padx=(0, PAD_X))
        return e

    def _lbl_combo(self, parent, label: str, key: str,
                   values: list, width: int = 12):
        tk.Label(parent, text=label, bg=BG_PANEL,
                 fg=FG_LABEL, font=FONT_LABEL
                 ).pack(side="left", padx=(PAD_X, 2))
        self._vars[key] = tk.StringVar(value=values[0] if values else "")
        cb = ttk.Combobox(parent, textvariable=self._vars[key],
                          values=values, width=width, state="readonly",
                          font=FONT_ENTRY)
        # Style combobox
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox",
                         fieldbackground=BG_ENTRY,
                         background=FG_BUTTON_BG,
                         foreground=FG_ENTRY)
        cb.pack(side="left", padx=(0, PAD_X))
        return cb

    def _btn(self, text: str, parent, cmd,
             side="left", padx=4, bg=None) -> tk.Button:
        b = tk.Button(
            parent, text=text, command=cmd,
            bg=bg or FG_BUTTON_BG, fg=FG_BUTTON_FG,
            font=FONT_BTN,
            relief="raised", bd=2,
            padx=8, pady=3,
            cursor="hand2",
            activebackground=FG_BUTTON_HOV,
            activeforeground=FG_LABEL,
        )
        b.pack(side=side, padx=padx)
        return b

    # ══════════════════════════════════════════════════════════════════════════
    # Live preview binding
    # ══════════════════════════════════════════════════════════════════════════

    def _bind_preview_refresh(self):
        """Refresh drawing canvas whenever any key variable changes."""
        watch = ["size", "schedule", "material", "pressure_class",
                 "comp_type", "pipe_angle", "inlet_arm", "outlet_arm",
                 "pipe_spec", "line_no", "quantity"]
        for key in watch:
            if key in self._vars:
                self._vars[key].trace_add("write", lambda *_: self._refresh_canvas())

    def _refresh_canvas(self):
        def safe(key, default=""):
            try:
                return self._vars[key].get()
            except Exception:
                return default

        data = {
            "line_no":       safe("line_no"),
            "size":          safe("size", "6"),
            "schedule":      safe("schedule", "SCH 40"),
            "material":      safe("material", "CS"),
            "pressure_class":safe("pressure_class", "150#"),
            "pipe_spec":     safe("pipe_spec"),
            "comp_type":     safe("comp_type", "PIPE"),
            "angle":         safe("pipe_angle") or "90",
            "length":        safe("inlet_arm") or "6",
            "has_valve":     self._vars.get("branches",
                                tk.BooleanVar()).get(),
            "has_flange":    safe("inlet_flange") == "Standard",
        }
        try:
            data["size2"] = str(float(data["size"]) * 0.6)
        except Exception:
            data["size2"] = "4"

        self.canvas.update_data(data)

    # ══════════════════════════════════════════════════════════════════════════
    # Backend actions
    # ══════════════════════════════════════════════════════════════════════════

    def _get_project_data(self) -> dict:
        """Build a minimal project_data dict from the current form values."""
        def v(key, default=""):
            try:
                return self._vars[key].get().strip()
            except Exception:
                return default

        def fv(key, default=0.0):
            try:
                return float(self._vars[key].get().strip() or default)
            except Exception:
                return default

        comp = {
            "tag_no":         v("tag_no") or "ITEM-001",
            "comp_type":      v("comp_type", "PIPE"),
            "description":    v("comp_type", "Pipe Component"),
            "size":           v("size", "6"),
            "size_2":         None,
            "material":       v("material", "CS"),
            "schedule":       v("schedule", "SCH 40"),
            "pressure_class": v("pressure_class", "150#"),
            "quantity":       fv("quantity", 1.0),
            "unit":           v("unit", "EA"),
            "end_connection": "BW",
            "remarks":        "",
        }
        line_info = {
            "line_no":                v("line_no") or "LINE-001",
            "fluid":                  v("mat_spec") or "Process Fluid",
            "fluid_service":          v("fluid_service", "C"),
            "design_pressure_bar":    fv("design_pressure", 10.0),
            "design_temp_c":          fv("design_temp", 80.0),
            "operating_pressure_bar": fv("design_pressure", 10.0) * 0.8,
            "operating_temp_c":       fv("design_temp", 80.0) * 0.9,
            "pipe_spec":              v("pipe_spec") or "A1A",
            "insulation":             False,
            "heat_tracing":           False,
            "from_equip":             v("project_id") or "EQUIP-IN",
            "to_equip":               v("element_id") or "EQUIP-OUT",
        }
        return {"lines": [{"line_info": line_info, "components": [comp]}]}

    def _set_status(self, msg: str, color: str = "#AAFFAA"):
        self.status_var.set(msg)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _on_proceed(self):
        server = self._vars["server"].get().strip()
        self._set_status(f"Connected to server: {server}")
        messagebox.showinfo("Server", f"Connected to: {server}")

    def _on_new(self):
        for key, var in self._vars.items():
            try:
                if isinstance(var, tk.BooleanVar):
                    var.set(False)
                elif isinstance(var, tk.StringVar):
                    var.set("")
            except Exception:
                pass
        # Reset combobox defaults
        defaults = {
            "size": NOMINAL_PIPE_SIZES[8],
            "schedule": "SCH 40",
            "material": "CS",
            "pressure_class": "150#",
            "fluid_service": "C",
            "unit": "M",
            "comp_type": "PIPE",
            "inlet_flange": "Standard",
            "outlet_flange": "Standard",
            "resp_dept": "MECHANICAL",
        }
        for k, val in defaults.items():
            if k in self._vars:
                self._vars[k].set(val)
        self.canvas.update_data({})
        self._set_status("New form — all fields cleared.")

    def _on_open_json(self):
        path = filedialog.askopenfilename(
            title="Open JSON Project File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self._set_status(f"Opened: {path}")
            messagebox.showinfo("Open JSON",
                                f"File loaded:\n{path}\n\n"
                                "Click 'Run All' to process.")

    def _on_open_csv(self):
        path = filedialog.askopenfilename(
            title="Open CSV Line List",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self._set_status(f"CSV loaded: {path}")

    def _run_demo(self):
        from data.sample_project import SAMPLE_PROJECT
        self._set_status("Running DEMO project...")
        self._execute_pipeline(SAMPLE_PROJECT, "Demo_Project")

    def _run_validate(self):
        data = self._get_project_data()
        proc = ISOPipingProcessor()
        lines = proc.process(data)
        val = PipingValidator()
        results = val.validate_project(lines)

        errors   = results["total_errors"]
        warnings = results["total_warnings"]

        if errors == 0:
            color = PASS_COLOR
            icon  = "Validation PASSED"
        else:
            color = FAIL_COLOR
            icon  = f"Validation FAILED — {errors} error(s)"

        self._set_status(f"{icon}  |  {warnings} warning(s)")

        detail = ""
        for ln, res in results["details"].items():
            detail += f"\n[{'PASS' if res['passed'] else 'FAIL'}]  {ln}\n"
            for e in res["errors"]:
                detail += f"  ERROR: {e}\n"
            for w in res["warnings"]:
                detail += f"  WARN : {w}\n"

        messagebox.showinfo("Validation Results",
                            f"{icon}\nWarnings: {warnings}\n{detail}")

    def _run_bom(self):
        data = self._get_project_data()
        proc = ISOPipingProcessor()
        lines = proc.process(data)
        proj  = self._vars.get("project_id", tk.StringVar()).get() or "Project"
        bom   = BOMGenerator(project_name=proj)
        path  = bom.export_consolidated_csv(lines)
        self._set_status(f"BOM generated: {path}")
        messagebox.showinfo("BOM Generated",
                            f"Consolidated BOM saved to:\n{path}")

    def _run_iso(self):
        data = self._get_project_data()
        proc = ISOPipingProcessor()
        lines = proc.process(data)
        proj  = self._vars.get("project_id", tk.StringVar()).get() or "Project"
        iso   = ISODrawingGenerator(project_name=proj)
        result = iso.generate_all(lines)
        paths = "\n".join(result["scripts"] + result["reports"])
        self._set_status(f"ISO scripts & reports generated ({len(lines)} line(s))")
        messagebox.showinfo("ISO Generated", f"Files created:\n{paths}")

    def _run_all(self):
        data = self._get_project_data()
        proj = self._vars.get("project_id", tk.StringVar()).get() or "Project"
        self._execute_pipeline(data, proj)

    def _execute_pipeline(self, project_data: dict, project_name: str):
        try:
            proc  = ISOPipingProcessor()
            lines = proc.process(project_data)
            s     = proc.summary()

            val     = PipingValidator()
            vres    = val.validate_project(lines)

            bom     = BOMGenerator(project_name=project_name)
            csv_p   = bom.export_consolidated_csv(lines)
            xls_p   = bom.export_excel(lines)
            rpt_p   = bom.generate_summary_report(lines)

            iso     = ISODrawingGenerator(project_name=project_name)
            iso_res = iso.generate_all(lines)

            msg = (
                f"Project: {project_name}\n"
                f"Lines: {s['total_lines']}  |  Components: {s['total_components']}\n"
                f"Total Weight: {s['total_weight_kg']} kg\n\n"
                f"Validation: {vres['lines_passed']}/{vres['lines_checked']} passed  "
                f"|  {vres['total_errors']} error(s)  "
                f"|  {vres['total_warnings']} warning(s)\n\n"
                f"BOM CSV:   {csv_p}\n"
                f"BOM Excel: {xls_p or 'skipped (install openpyxl)'}\n"
                f"Summary:   {rpt_p}\n\n"
                f"AutoCAD scripts: {len(iso_res['scripts'])}\n"
                f"ISO reports:     {len(iso_res['reports'])}\n\n"
                f"Output folder: output/"
            )
            self._set_status(
                f"Done — {s['total_lines']} lines | "
                f"{s['total_components']} components | "
                f"{s['total_weight_kg']} kg"
            )
            messagebox.showinfo("Automation Complete", msg)

        except Exception as exc:
            self._set_status(f"ERROR: {exc}")
            messagebox.showerror("Error", str(exc))


# ─────────────────────────────────────────────────────────────────────────────
def launch():
    app = ISOPipingApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
