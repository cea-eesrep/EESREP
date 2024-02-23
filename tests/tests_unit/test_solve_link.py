
from os import environ

import numpy as np
import pandas as pd
from eesrep.eesrep_io import ComponentIO
import pytest

import eesrep
from eesrep.components.converter import Converter
from eesrep.components.generic_component import GenericComponent
from eesrep.components.sink_source import FatalSink, Source
from eesrep.eesrep_enum import TimeSerieType
from eesrep.eesrep_exceptions import UndefinedTimeRangeException
from eesrep.solver_interface.generic_interface import GenericInterface

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "docplex"

def make_basic_model(model:eesrep.Eesrep, coeff:float, offset:float):
    source = Source("source", 0., 100., 1.)
    model.add_component(source)
    load = FatalSink("load", pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]}))
    model.add_component(load)

    model.add_link(source.power_out, load.power_in, coeff, offset)

def make_basic_model_with_bus(model:eesrep.Eesrep, revert:bool, coeff:float, offset:float):
    source = Source("source", -100., 100., 1.)
    model.add_component(source)
    model.create_bus("bus", {"name":"bus"})

    load = FatalSink("load", pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]}))
    model.add_component(load)
    
    if revert:
        model.plug_to_bus(source.power_out, "bus", True, 1., 0.)
        model.plug_to_bus(load.power_in, "bus", True, coeff, offset)
    else:
        model.plug_to_bus(source.power_out, "bus", False, 1., 0.)
        model.plug_to_bus(load.power_in, "bus", True, coeff, offset)


@pytest.mark.Unit
@pytest.mark.solve
def test_solve_too_early():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.solve()
        assert False, "Cant solve before defining time range"
    except UndefinedTimeRangeException:
        assert True

@pytest.mark.Unit
@pytest.mark.solve
def test_get_results_too_early():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.get_results()
        assert False, "Cant get results before solving."
    except Exception:
        assert True

@pytest.mark.Unit
@pytest.mark.solve
def test_solve_horizon():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 5)
    make_basic_model(model, 1., 0.)
    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["load_power_in"].values - np.array([1, 2, 3, 4, 5]))) == 0, "Error in solving horizon"
    assert np.max(np.abs(results["source_power_out"].values - np.array([1, 2, 3, 4, 5]))) == 0, "Error in solving horizon"

@pytest.mark.Unit
@pytest.mark.solve
def test_solve_get_results():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 5)
    make_basic_model(model, 1., 0.)
    model.solve()

    results_df = model.get_results(as_dataframe=True)
    results = model.get_results(as_dataframe=False)
    
    assert np.max(np.abs(results_df["load_power_in"].values - np.array(results["load"]["power_in"]))) == 0, "Error in dict construction"
    assert np.max(np.abs(results_df["source_power_out"].values - np.array(results["source"]["power_out"]))) == 0, "Error in dict construction"

    
@pytest.mark.Unit
@pytest.mark.solve
def test_solve_coeff():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 2)
    make_basic_model(model, 2., 0.)
    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["load_power_in"].values - np.array([1, 2]))) == 0, "Error in link coeff implementation"
    assert np.max(np.abs(results["source_power_out"].values - np.array([.5, 1]))) == 0, "Error in link coeff implementation"


@pytest.mark.Unit
@pytest.mark.solve
def test_solve_offset():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 2)
    make_basic_model(model, 1., -2.)
    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["load_power_in"].values - np.array([1, 2]))) == 0, "Error in link offset implementation"
    assert np.max(np.abs(results["source_power_out"].values - np.array([3, 4]))) == 0, "Error in link offset implementation"

    
    
@pytest.mark.Unit
@pytest.mark.solve
def test_solve_coeff_bus():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 2)

    make_basic_model_with_bus(model, False, 2., 0.)

    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["load_power_in"].values - np.array([1, 2]))) == 0, "Error in bus coeff implementation"
    assert np.max(np.abs(results["source_power_out"].values - np.array([2, 4]))) == 0, "Error in bus coeff implementation"

    
@pytest.mark.Unit
@pytest.mark.solve
def test_solve_offset_bus():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 2)

    make_basic_model_with_bus(model, False, 1., 2.)

    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["load_power_in"].values - np.array([1, 2]))) == 0, "Error in bus offset implementation"
    assert np.max(np.abs(results["source_power_out"].values - np.array([3, 4]))) == 0, "Error in bus offset implementation"
    
@pytest.mark.Unit
@pytest.mark.solve
def test_solve_coeff_revert_direction():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 2)

    make_basic_model_with_bus(model, True, 1., 0.)

    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["load_power_in"].values - np.array([1, 2]))) == 0, "Error in solving horizon"
    assert np.max(np.abs(results["source_power_out"].values - np.array([-1, -2]))) == 0, "Error in solving horizon"

    
@pytest.mark.Unit
@pytest.mark.solve
def test_solve_greater_than():
    """
        Tests if the cluster starts the right amount of machines
    """
    
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name

            self.time_series = {}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var": ComponentIO(self.name, "intensive_var", TimeSerieType.INTENSIVE, False)
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            variables["intensive_var"] = model_interface.get_new_continuous_variable_list(component_name+"_intensive_var_", len(time_steps), 0, 10)

            for i in range(len(time_steps)):
                model_interface.add_equality(variables["intensive_var"][i], 5)

            objective = model_interface.sum_variables(variables["intensive_var"])

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 5)
    model.add_component(FakeComponent("fake"))
    model.solve()

    results_df = model.get_results(as_dataframe=True)
    
    assert np.min(results_df["fake_intensive_var"].values) == 5, "Results should be greater than 5"
    
@pytest.mark.Unit
@pytest.mark.solve
def test_solve_lower_than():
    """
        Tests if the cluster starts the right amount of machines
    """
    
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name

            self.time_series = {}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var": ComponentIO(self.name, "intensive_var", TimeSerieType.INTENSIVE, False)
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            variables["intensive_var"] = model_interface.get_new_continuous_variable_list(component_name+"_intensive_var_", len(time_steps), 0, 10)

            for i in range(len(time_steps)):
                model_interface.add_lower_than(variables["intensive_var"][i], 5)

            objective = - model_interface.sum_variables(variables["intensive_var"])

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 5)
    model.add_component(FakeComponent("fake"))
    model.solve()

    results_df = model.get_results(as_dataframe=True)
    
    assert np.max(results_df["fake_intensive_var"].values) == 5, "Results should be lower than 5"
    


@pytest.mark.Unit
@pytest.mark.solve
def test_history():
    """
        Tests if the cluster starts the right amount of machines
    """
    
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name

            self.time_series = {}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var": ComponentIO(self.name, "intensive_var", TimeSerieType.INTENSIVE, True)
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):

            variables = {}
            variables["intensive_var"] = model_interface.get_new_continuous_variable_list(component_name+"_intensive_var_", len(time_steps), 0, 10000)

            for i in range(len(time_steps)):
                if len(history) > 0:
                    model_interface.add_equality(variables["intensive_var"][i], history["intensive_var"].loc[len(history)-1]+1)
                else:
                    model_interface.add_equality(variables["intensive_var"][i], 0)

            objective = model_interface.sum_variables(variables["intensive_var"])

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 1, 5)
    model.add_component(FakeComponent("fake"))
    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["fake_intensive_var"].values - np.array([0, 1, 2, 3, 4]))) == 0, "Error in solving horizon"


@pytest.mark.Unit
@pytest.mark.solve
def test_solve_maximize():
    """
        Tests if the cluster starts the right amount of machines
    """
    
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name

            self.time_series = {}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var": ComponentIO(self.name, "intensive_var", TimeSerieType.INTENSIVE, False)
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            variables["intensive_var"] = model_interface.get_new_continuous_variable_list(component_name+"_intensive_var_", len(time_steps), 0, 10)

            objective = model_interface.sum_variables(variables["intensive_var"])

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests, direction="Maximize")
    model.define_time_range(1., 1, 5, 1)
    model.add_component(FakeComponent("fake"))
    model.solve()

    results_df = model.get_results(as_dataframe=True)
    
    assert np.average(results_df["fake_intensive_var"].values) == 10, "Results should always be at 10, its maximum."
    
