
from os import environ
import pytest

import pandas as pd

import eesrep
from eesrep.solver_interface.docplex_interface import DocplexInterface

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "docplex"

@pytest.mark.Unit
@pytest.mark.interface_registration
def test_existing_interface():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model.register_solver_interface("docplex", DocplexInterface)
        assert False, "Accepted to add an existing interface"
    except ValueError:
        assert True

@pytest.mark.Unit
@pytest.mark.interface_registration
@pytest.mark.valid_interface
def test_valid_interface():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model.register_solver_interface("other_cplex", DocplexInterface)
        assert True
    except ValueError:
        assert False, "Refused valid interface"


@pytest.mark.Unit
@pytest.mark.interface_registration
def test_wrong_interface_name():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(interface="wrong_interface_name")

    try:
        model.create_model_interface()
        assert False, "Interface name does not exist"
    except ValueError:
        assert True

