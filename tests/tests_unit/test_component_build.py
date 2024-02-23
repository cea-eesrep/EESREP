
from os import environ
from eesrep.eesrep_enum import TimeSerieType
from eesrep.eesrep_io import ComponentIO
import pytest

import pandas as pd

import eesrep
from eesrep.eesrep_io import ComponentIO

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "docplex"

@pytest.mark.Unit
@pytest.mark.component_io
def test_wrong_component_io_component_name_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    try:
        io = ComponentIO(True, "input", TimeSerieType.INTENSIVE, False)
        assert False, "ComponentIO component name should be a string"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component_io
def test_wrong_component_io_io_name_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    try:
        io = ComponentIO("component", 12., TimeSerieType.INTENSIVE, False)
        assert False, "ComponentIO io name should be a string"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component_io
def test_wrong_component_io_type_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    try:
        io = ComponentIO("component", "input", "INTENSIVE", False)
        assert False, "ComponentIO type should be a string"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component_io
def test_wrong_component_io_continuity_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    try:
        io = ComponentIO("component", "input", TimeSerieType.INTENSIVE, "False")
        assert False, "ComponentIO continuity should be a string"
    except TypeError:
        assert True
