
from os import environ

import pandas as pd
from eesrep.eesrep_io import ComponentIO
import pytest

import eesrep
from eesrep.components.generic_component import GenericComponent
from eesrep.eesrep_enum import TimeSerieType
from eesrep.eesrep_exceptions import (BusNameException, ComponentIOException,
                                      ComponentNameException)
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.test_interface_solver import get_couple_from_key

solver_for_tests, interface_for_tests = get_couple_from_key()


class FakeComponent(GenericComponent):
    def __init__(self, name:str, intensive_ts:pd.DataFrame = pd.DataFrame(), extensive_ts:pd.DataFrame = pd.DataFrame()):
        self.name = name

        self.time_series = {}    
        if not intensive_ts.empty:
            self.time_series["intensive_ts"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": intensive_ts
                                            }
                                            
        if not extensive_ts.empty:
            self.time_series["extensive_ts"]={
                                                    "type": TimeSerieType.EXTENSIVE,
                                                    "value": extensive_ts
                                                }
        self.intensive_var = ComponentIO(self.name, "intensive_var", TimeSerieType.INTENSIVE, False)
        self.extensive_var = ComponentIO(self.name, "extensive_var", TimeSerieType.EXTENSIVE, False)

    def io_from_parameters(self) -> dict:
        return { 
                    "intensive_var": self.intensive_var,
                    "extensive_var": self.extensive_var
                }

    def build_model(self,
        component_name:str,
        time_steps:list,
        time_series:pd.DataFrame,
        history:pd.DataFrame,
        model_interface:GenericInterface):
        pass


@pytest.mark.Unit
@pytest.mark.link
def test_solve_link_wrong_component_1():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    wrong_component = FakeComponent("wrong_component")
    fake = FakeComponent("fake")
    model.add_component(fake)
    
    try:
        model.add_link(wrong_component.intensive_var, fake.intensive_var, 1., 0.)
        assert False, "Component does not exist"
    except ComponentNameException:
        assert True


@pytest.mark.Unit
@pytest.mark.link
def test_solve_link_wrong_component_2():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    wrong_component = FakeComponent("wrong_component")
    fake = FakeComponent("fake")
    model.add_component(fake)
    
    try:
        model.add_link(fake.intensive_var, wrong_component.intensive_var, 1., 0.)
        assert False, "Component does not exist"
    except ComponentNameException:
        assert True
        

@pytest.mark.Unit
@pytest.mark.link
def test_solve_link_wrong_component_1_variable():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fake = FakeComponent("fake")
    fake2 = FakeComponent("fake2")
    model.add_component(fake)
    model.add_component(fake2)
    
    try:
        model.add_link(ComponentIO("fake", "var", TimeSerieType.INTENSIVE, False), fake2.intensive_var, 1., 0.)
        assert False, "Component variable does not exist"
    except ComponentIOException:
        assert True


@pytest.mark.Unit
@pytest.mark.link
def test_solve_link_wrong_component_2_variable():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fake = FakeComponent("fake")
    model.add_component(fake)
    fake2 = FakeComponent("fake2")
    model.add_component(fake2)
    
    try:
        model.add_link(fake.intensive_var, ComponentIO("fake", "var", TimeSerieType.INTENSIVE, False), 1., 0.)
        assert False, "Component variable does not exist"
    except ComponentIOException:
        assert True

        
