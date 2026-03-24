"""
ISO Piping Automation — Main Entry Point
=========================================
Automates the generation of:
  • Validated piping line data
  • Bill of Materials (BOM) — CSV and Excel
  • AutoCAD isometric drawing scripts (.scr)
  • Isometric drawing data reports

Usage:
  python main.py --input data/sample_project.json
  python main.py --lines data/line_list.csv --components data/components.csv
  python main.py --input data/sample_project.json --bom-only
  python main.py --input data/sample_project.json --validate-only
"""

import os
import sys
import argparse
import json
from datetime import date

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))

from core.processor import ISOPipingProcessor
from core.validator import PipingValidator
from core.bom_generator import BOMGenerator
from core.iso_generator import ISODrawingGenerator
from utils.data_reader import read_json, merge_csv_data
from config.settings import OUTPUT_DIR, REPORTS_DIR, SCRIPTS_DIR, DRAWINGS_DIR


def print_banner():
    print("=" * 60)
    print("  ISO PIPING AUTOMATION PROGRAM")
    print("  AutoCAD Piping | BOM | Isometric Drawing Generator")
    print(f"  Date: {date.today()}")
    print("=" * 60)
    print()


def print_validation_results(results: dict):
    print("\n--- VALIDATION RESULTS ---")
    print(f"Lines checked : {results['lines_checked']}")
    print(f"Lines passed  : {results['lines_passed']}")
    print(f"Total errors  : {results['total_errors']}")
    print(f"Total warnings: {results['total_warnings']}")
    print()
    for line_no, res in results["details"].items():
        status = "PASS" if res["passed"] else "FAIL"
        print(f"  [{status}] {line_no}")
        for e in res["errors"]:
            print(f"         ERROR   : {e}")
        for w in res["warnings"]:
            print(f"         WARNING : {w}")
    print()


def run_automation(project_data: dict, project_name: str,
                   validate_only: bool = False,
                   bom_only: bool = False,
                   skip_autocad: bool = False):
    """Core automation pipeline."""

    # 1. Process project data
    print("[1/4] Processing piping data...")
    processor = ISOPipingProcessor()
    lines = processor.process(project_data)
    summary = processor.summary()
    print(f"      Lines processed : {summary['total_lines']}")
    print(f"      Components      : {summary['total_components']}")
    print(f"      Total weight    : {summary['total_weight_kg']} kg")

    # 2. Validate
    print("\n[2/4] Validating piping specifications...")
    validator = PipingValidator()
    val_results = validator.validate_project(lines)
    print_validation_results(val_results)

    if validate_only:
        print("Validation-only mode — stopping here.")
        return

    if val_results["total_errors"] > 0:
        print(f"WARNING: {val_results['total_errors']} validation error(s) found.")
        print("         Proceeding with generation (review errors in reports).\n")

    # 3. Generate BOM
    print("[3/4] Generating Bill of Materials...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    bom_gen = BOMGenerator(project_name=project_name, output_dir=REPORTS_DIR)

    cons_csv = bom_gen.export_consolidated_csv(lines)
    print(f"      Consolidated BOM (CSV) : {cons_csv}")

    excel_path = bom_gen.export_excel(lines)
    if excel_path:
        print(f"      BOM Excel workbook     : {excel_path}")
    else:
        print("      BOM Excel skipped (openpyxl not installed)")

    summary_rpt = bom_gen.generate_summary_report(lines)
    print(f"      Summary report         : {summary_rpt}")

    if bom_only:
        print("\nBOM-only mode — stopping here.")
        return

    # 4. Generate ISO drawings & AutoCAD scripts
    print("\n[4/4] Generating ISO drawing data and AutoCAD scripts...")
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    os.makedirs(DRAWINGS_DIR, exist_ok=True)
    iso_gen = ISODrawingGenerator(
        project_name=project_name,
        scripts_dir=SCRIPTS_DIR,
        drawings_dir=DRAWINGS_DIR,
    )
    gen_results = iso_gen.generate_all(lines)

    for scr in gen_results["scripts"]:
        print(f"      AutoCAD script : {scr}")
    for rpt in gen_results["reports"]:
        print(f"      ISO report     : {rpt}")

    print("\n" + "=" * 60)
    print("  AUTOMATION COMPLETE")
    print(f"  Output directory: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="ISO Piping Automation — BOM, Validation, AutoCAD Script Generator"
    )
    parser.add_argument("--input", "-i",
                        help="Path to JSON project file")
    parser.add_argument("--lines", "-l",
                        help="Path to CSV line list file")
    parser.add_argument("--components", "-c",
                        help="Path to CSV components file")
    parser.add_argument("--project-name", "-p", default="Project",
                        help="Project name for output files (default: Project)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only run validation checks, no output generated")
    parser.add_argument("--bom-only", action="store_true",
                        help="Generate BOM only, skip drawing generation")
    parser.add_argument("--skip-autocad", action="store_true",
                        help="Skip AutoCAD script generation")
    parser.add_argument("--demo", action="store_true",
                        help="Run with built-in demo data")

    args = parser.parse_args()

    # Load project data
    if args.demo:
        from data.sample_project import SAMPLE_PROJECT
        project_data = SAMPLE_PROJECT
        project_name = "Demo_Project"
        print("Running in DEMO mode with built-in sample data.\n")
    elif args.input:
        if not os.path.exists(args.input):
            print(f"ERROR: Input file not found: {args.input}")
            sys.exit(1)
        project_data = read_json(args.input)
        project_name = args.project_name
    elif args.lines and args.components:
        for p in (args.lines, args.components):
            if not os.path.exists(p):
                print(f"ERROR: File not found: {p}")
                sys.exit(1)
        project_data = merge_csv_data(args.lines, args.components)
        project_name = args.project_name
    else:
        print("No input provided. Running in DEMO mode.\n")
        from data.sample_project import SAMPLE_PROJECT
        project_data = SAMPLE_PROJECT
        project_name = "Demo_Project"

    run_automation(
        project_data=project_data,
        project_name=project_name,
        validate_only=args.validate_only,
        bom_only=args.bom_only,
        skip_autocad=args.skip_autocad,
    )


if __name__ == "__main__":
    main()
