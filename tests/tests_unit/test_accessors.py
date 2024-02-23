
from os import environ
import pytest

import eesrep
from eesrep.components.converter import Converter

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "docplex"


@pytest.mark.Unit
@pytest.mark.accessors
def test_access_components():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    assert len(model.get_components()) == 0, "Component list should be empty"

    converter = Converter("converter", 1., 0., 1.)
    model.add_component(converter)

    assert len(model.get_components()) == 1, "Component list should contain one component"

    converter2 = Converter("converter2", 1., 0., 1.)
    model.add_component(converter2)

    assert len(model.get_components()) == 2, "Component list should contain two components"


@pytest.mark.Unit
@pytest.mark.accessors
def test_access_variables():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    assert model.get_variables() == {}, "The model should not have any variable yet"

    converter = Converter("converter", 1., 0., 1.)
    model.add_component(converter)

    assert model.get_variables() == {}, "The model should not have any variable yet"

    model.define_time_range(1., 1, 5, 1)
    model._init_time_step()
    
    assert list(model.get_variables().keys()) == ['converter'], "The variables should be sorted by component"
    assert list(model.get_variables()['converter'].keys()) == ['power_in', 'power_out'], "The variables of a component should be sorted by variable"

    for key in model.get_variables()['converter'].keys():
        assert len(model.get_variables()['converter'][key]) == 5, f"{key} variable list should be 5 long."


@pytest.mark.Unit
@pytest.mark.accessors
def test_get_component_time_series_wrong_component():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model.get_component_time_series('zfafaz')
        assert False, "Returned wrong component name time_series."
    except:
        assert True
    
@pytest.mark.Unit
@pytest.mark.accessors
def test_get_component_time_series():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    converter = Converter("converter", 1., 0., 1.)
    model.add_component(converter)

    assert model.get_component_time_series('converter') == Converter("converter", 1., 0., 1.).time_series, "Returned wrong component time series"

    

@pytest.mark.Unit
@pytest.mark.accessors
def test_get_component_variables_wrong_component():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model.get_component_io('converter')
        assert False, "Returned wrong component name variables."
    except:
        assert True
    
@pytest.mark.Unit
@pytest.mark.accessors
def test_get_component_variables():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    converter = Converter("converter", 1., 0., 1.)
    model.add_component(converter)

    assert model.get_component_io('converter') == Converter("converter", 1., 0., 1.).io_from_parameters(), "Returned wrong component variables"


@pytest.mark.Unit
@pytest.mark.accessors
def test_get_component_model():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.create_model_interface()
    
    assert model.get_model() is not None, "Failed returning the component model"
