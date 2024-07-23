
from os import environ
import pytest

import eesrep
from eesrep.eesrep_exceptions import BusNameException, BusTypeException, ComponentNameException, ParametersException
from eesrep.test_interface_solver import get_couple_from_key
from eesrep.components.bus import GenericBus
from eesrep.components.tool import LowerThan

solver_for_tests, interface_for_tests = get_couple_from_key()

@pytest.mark.Unit
@pytest.mark.bus
def test_plug_bus_wrong_type():
    """
        Tests if the bus plugged to is actually a genericBus
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    component_1 = LowerThan("component_1", 0.)
    component_not_a_bus = LowerThan("component_not_a_bus", 0.)
    
    model.add_component(component_1)
    model.add_component(component_not_a_bus)

    try:
        model.plug_to_bus(component_1.power_in, component_not_a_bus.power_in, 1., 0.)
        assert False, "component_not_a_bus is not in the bus list"
    except BusNameException:
        assert True

@pytest.mark.Unit
@pytest.mark.bus
def test_unknown_component():
    """
        Tests if the bus plugged to is actually a genericBus
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    component_1 = LowerThan("component_1", 0.)
    component_bus = GenericBus("component_bus")
    
    model.add_component(component_bus)

    try:
        model.plug_to_bus(component_1.power_in, component_bus.input, 1., 0.)
        assert False, "component_1 is not declared"
    except ComponentNameException:
        assert True

@pytest.mark.Unit
@pytest.mark.bus
def test_unknown_bus():
    """
        Tests if the bus plugged to is actually a genericBus
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    component_1 = LowerThan("component_1", 0.)
    component_bus = GenericBus("component_bus")
    
    model.add_component(component_1)

    try:
        model.plug_to_bus(component_1.power_in, component_bus.input, 1., 0.)
        assert False, "component_bus is not declared"
    except BusNameException:
        assert True
        
@pytest.mark.Unit
@pytest.mark.bus
def test_bus_added_as_input():
    """
        Tests if the bus plugged to is actually a genericBus
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    component_1 = LowerThan("component_1", 0.)
    component_bus = GenericBus("component_bus")
    
    model.add_component(component_1)
    model.add_component(component_bus)

    model.plug_to_bus(component_1.power_in, component_bus.input, 1., 0.)
    assert [component_1.power_in, 1., 0.] in model._Eesrep__buses[component_bus.name].inputs, "component_1.power_in is not in component_bus inputs."


@pytest.mark.Unit
@pytest.mark.bus
def test_bus_added_as_output():
    """
        Tests if the bus plugged to is actually a genericBus
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    component_1 = LowerThan("component_1", 0.)
    component_bus = GenericBus("component_bus")
    
    model.add_component(component_1)
    model.add_component(component_bus)

    model.plug_to_bus(component_1.power_in, component_bus.output, 1., 0.)
    assert [component_1.power_in, 1., 0.] in model._Eesrep__buses[component_bus.name].outputs, "component_1.power_in is not in component_bus inputs."

