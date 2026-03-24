"""
Unit tests for the ISO Piping Automation pipeline.
Run: python -m pytest tests/ -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.processor import ISOPipingProcessor
from core.validator import PipingValidator
from core.models import PipeLine, PipeComponent
from data.sample_project import SAMPLE_PROJECT


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture
def processor():
    return ISOPipingProcessor()


@pytest.fixture
def validator():
    return PipingValidator()


@pytest.fixture
def processed_lines(processor):
    return processor.process(SAMPLE_PROJECT)


# ------------------------------------------------------------------ #
# Processor tests
# ------------------------------------------------------------------ #
class TestISOPipingProcessor:

    def test_process_returns_correct_number_of_lines(self, processed_lines):
        assert len(processed_lines) == 3

    def test_line_no_assigned_correctly(self, processed_lines):
        line_nos = [l.line_no for l in processed_lines]
        assert "6\"-PW-1001-A1A" in line_nos
        assert "4\"-SH-2001-B3B" in line_nos
        assert "1\"-CD-3001-C1C" in line_nos

    def test_components_loaded(self, processed_lines):
        line = processed_lines[0]
        assert line.component_count == 5

    def test_pipe_weight_calculated(self, processed_lines):
        # All pipes should have weight > 0
        for line in processed_lines:
            for comp in line.components:
                assert comp.weight_kg >= 0, f"{comp.tag_no} has negative weight"

    def test_total_weight_positive(self, processed_lines):
        for line in processed_lines:
            assert line.total_weight_kg > 0

    def test_component_line_no_assigned(self, processed_lines):
        for line in processed_lines:
            for comp in line.components:
                assert comp.line_no == line.line_no

    def test_pipe_weight_per_m(self):
        p = ISOPipingProcessor()
        w = p.calc_pipe_weight_per_m("6", "SCH 40")
        # 6" SCH40 is ~28 kg/m — allow wide tolerance for formula-based calc
        assert 10.0 < w < 60.0, f"Unexpected weight: {w}"

    def test_summary_keys(self, processed_lines):
        proc = ISOPipingProcessor()
        proc.lines = processed_lines
        s = proc.summary()
        assert "total_lines" in s
        assert "total_components" in s
        assert "total_weight_kg" in s


# ------------------------------------------------------------------ #
# Validator tests
# ------------------------------------------------------------------ #
class TestPipingValidator:

    def test_valid_project_passes(self, validator, processed_lines):
        results = validator.validate_project(processed_lines)
        assert results["total_errors"] == 0, results

    def test_invalid_pressure_fails(self, validator):
        line = PipeLine(
            line_no="TEST-001",
            fluid="Water",
            fluid_service="C",
            design_pressure_bar=10.0,
            design_temp_c=80.0,
            operating_pressure_bar=15.0,   # exceeds design!
            operating_temp_c=60.0,
            pipe_spec="A1A",
        )
        ok, errors, _ = validator.validate_line(line)
        assert not ok
        assert any("operating pressure" in e.lower() for e in errors)

    def test_invalid_fluid_service_fails(self, validator):
        line = PipeLine(
            line_no="TEST-002",
            fluid="Unknown",
            fluid_service="Z",   # invalid
            design_pressure_bar=5.0,
            design_temp_c=50.0,
            operating_pressure_bar=4.0,
            operating_temp_c=40.0,
            pipe_spec="A1A",
        )
        ok, errors, _ = validator.validate_line(line)
        assert not ok
        assert any("fluid service" in e.lower() for e in errors)

    def test_invalid_component_size_fails(self, validator):
        comp = PipeComponent(
            item_no=1,
            tag_no="TEST-COMP",
            comp_type="PIPE",
            description="Test Pipe",
            size="999",   # invalid size
            size_2=None,
            material="CS",
            schedule="SCH 40",
            pressure_class="150#",
            quantity=5.0,
            unit="M",
        )
        ok, errors, _ = validator.validate_component(comp)
        assert not ok
        assert any("999" in e for e in errors)

    def test_service_b_warning(self, validator, processed_lines):
        # Line 2 is service B — should generate ASME warning
        line2 = next(l for l in processed_lines if "2001" in l.line_no)
        _, _, warnings = validator.validate_line(line2)
        assert any("category b" in w.lower() or "radiograph" in w.lower()
                   for w in warnings)

    def test_empty_components_warning(self, validator):
        line = PipeLine(
            line_no="EMPTY-001",
            fluid="Air",
            fluid_service="D",
            design_pressure_bar=3.0,
            design_temp_c=40.0,
            operating_pressure_bar=2.0,
            operating_temp_c=30.0,
            pipe_spec="D1A",
        )
        ok, errors, warnings = validator.validate_line(line)
        assert ok
        assert any("no components" in w.lower() for w in warnings)


# ------------------------------------------------------------------ #
# Model tests
# ------------------------------------------------------------------ #
class TestModels:

    def test_pipeline_add_component_sets_line_no(self):
        line = PipeLine(
            line_no="L-001",
            fluid="Water",
            fluid_service="C",
            design_pressure_bar=5.0,
            design_temp_c=50.0,
            operating_pressure_bar=4.0,
            operating_temp_c=40.0,
            pipe_spec="A1A",
        )
        comp = PipeComponent(
            item_no=1, tag_no="P-001", comp_type="PIPE",
            description="Pipe", size="4", size_2=None,
            material="CS", schedule="SCH 40", pressure_class="150#",
            quantity=5.0, unit="M",
        )
        line.add_component(comp)
        assert comp.line_no == "L-001"
        assert line.component_count == 1

    def test_component_to_dict(self):
        comp = PipeComponent(
            item_no=1, tag_no="P-001", comp_type="PIPE",
            description="Test Pipe", size="6", size_2=None,
            material="CS", schedule="SCH 40", pressure_class="150#",
            quantity=10.0, unit="M",
        )
        d = comp.to_dict()
        assert d["Size (inch)"] == "6"
        assert d["Material"] == "CS"

    def test_reducer_size_display(self):
        comp = PipeComponent(
            item_no=1, tag_no="RED-001", comp_type="FITTING",
            description="Reducer", size="6", size_2="4",
            material="CS", schedule="SCH 40", pressure_class="150#",
            quantity=1, unit="EA",
        )
        d = comp.to_dict()
        assert d["Size (inch)"] == "6 x 4"
