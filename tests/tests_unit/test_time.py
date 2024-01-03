
from os import environ
import pytest

import pandas as pd

import eesrep
from eesrep.eesrep_exceptions import UndefinedTimeRangeException

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "cplex"

@pytest.mark.Unit
@pytest.mark.time
def test_define_time_range():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 50, 1)

    assert model.time_step == 1., "Time step not set properly"
    assert model.time_shift  == 1, "Time shift not set properly"
    assert model.future_size == 50, "Future size not set properly"
    assert model.horizon_count  == 1, "Horizon count not set properly"

    assert model.custom_steps == [1 for _ in range(50)]
    
@pytest.mark.Unit
@pytest.mark.time
def test_define_time_range_twice():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 50, 1)

    try:
        model.define_time_range(1., 1, 50, 1)
        assert False, "define_time_range accepted twice"
    except:
        assert True

@pytest.mark.Unit
@pytest.mark.time
def test_set_custom_steps_wrong():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 50, 1)

    try:
        model.set_custom_steps([1., 1.])
        assert False, "define_time_range accepted twice"
    except:
        assert True

@pytest.mark.Unit
@pytest.mark.time
def test_set_custom_steps_too_early():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model.set_custom_steps(list(range(50)))
        assert False, "set_custom_steps accepted before define_time_range"
    except:
        assert True

@pytest.mark.Unit
@pytest.mark.time
def test_set_custom_steps():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 50, 1)
    model.set_custom_steps(list(range(50)))

    assert model.custom_steps == [i for i in range(50)]
    
@pytest.mark.Unit
@pytest.mark.time
def test_current_time_step():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(.5, 1, 50, 1)

    assert model._Eesrep__make_time_steps() == [0.5*i for i in range(51)]
    
@pytest.mark.Unit
@pytest.mark.time
def test_early_make_time_step():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model._Eesrep__make_time_steps()
        assert False, "Shouldn't make time steps before defining time steps."
    except UndefinedTimeRangeException:
        assert True