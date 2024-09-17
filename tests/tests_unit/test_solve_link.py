
from os import environ
import os

from eesrep.components.bus import GenericBus
import numpy as np
import pandas as pd
from eesrep.eesrep_io import ComponentIO
import pytest

import eesrep
from eesrep.components.generic_component import GenericComponent
from eesrep.components.sink_source import FatalSink, Source
from eesrep.eesrep_enum import SolverOption, TimeSerieType
from eesrep.eesrep_exceptions import ComponentIOException, ComponentNameException, UndefinedTimeRangeException
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.test_interface_solver import get_couple_from_key

solver_for_tests, interface_for_tests = get_couple_from_key()

def make_basic_model(model:eesrep.Eesrep, coeff:float, offset:float):
    source = Source("source", 0., 100., 1.)
    model.add_component(source)
    load = FatalSink("load", pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]}))
    model.add_component(load)

    model.add_link(source.power_out, load.power_in, coeff, offset)

def make_basic_model_with_bus(model:eesrep.Eesrep, revert:bool, coeff:float, offset:float):
    source = Source("source", -100., 100., 1.)
    model.add_component(source)

    bus = GenericBus("bus")
    model.add_component(bus)

    load = FatalSink("load", pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]}))
    model.add_component(load)
    
    if revert:
        model.plug_to_bus(source.power_out, bus.input, 1., 0.)
        model.plug_to_bus(load.power_in, bus.input, coeff, offset)
    else:
        model.plug_to_bus(source.power_out, bus.output, 1., 0.)
        model.plug_to_bus(load.power_in, bus.input, coeff, offset)


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
def test_solve_get_objective():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 3, 1)
    make_basic_model(model, 1., 0.)
    model.solve()

    assert model.get_objective_value() == 1+2+3, "Wrong objective returned."

@pytest.mark.Unit
@pytest.mark.solve
def test_solve_get_objective_multi_horizon():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.define_time_range(1., 1, 3, 3)
    make_basic_model(model, 1., 0.)
    model.solve()

    assert model.get_objective_value() == 1+2+3 + 2+3+4 + 3+4+5, "Wrong objective returned."
    
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
            model_interface:GenericInterface,
            future:pd.DataFrame = None):
            
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
            model_interface:GenericInterface,
            future:pd.DataFrame = None):
            
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
            model_interface:GenericInterface,
            future:pd.DataFrame = None):

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
            model_interface:GenericInterface,
            future:pd.DataFrame = None):
            
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

@pytest.mark.Unit
@pytest.mark.solve
def test_add_io_to_objective():
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source_1 = Source("source_1", 0., 100., 1.)
    source_2 = Source("source_2", 0., 100., 2.)

    model.add_component(source_1)
    model.add_component(source_2)

    bus = GenericBus("bus")
    model.add_component(bus)

    load = FatalSink("load", pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]}))
    model.add_component(load)
    
    model.plug_to_bus(source_1.power_out, bus.input, 1., 0.)
    model.plug_to_bus(source_2.power_out, bus.input, 1., 0.)
    model.plug_to_bus(load.power_in, bus.output, 1., 0.)

    model.add_io_to_objective(source_1.power_out, price=50.)
    model.define_time_range(1., 1, 5, 1)
    model.solve()

    results_df = model.get_results(as_dataframe=True)

    assert results_df["source_1_power_out"].max() == 0.

@pytest.mark.Unit
@pytest.mark.solve
def test_add_io_to_objective_wrong_component():
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source_1 = Source("source_1", 0., 100., 1.)

    try:
        model.add_io_to_objective(source_1.power_out, price=50.)
        assert False, "Adding to objective the IO of a not known component"
    except ComponentNameException:
        assert True
    

@pytest.mark.Unit
@pytest.mark.solve
def test_add_io_to_objective_wrong_io():
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source_1 = Source("source_1", 0., 100., 1.)
    model.add_component(source_1)

    try:
        model.add_io_to_objective(ComponentIO("source_1", "wrong_io", TimeSerieType.INTENSIVE, False), price=50.)
        assert False, "The provided IO does not exist for given component."
    except ComponentIOException:
        assert True


@pytest.mark.Unit
@pytest.mark.solve
def test_intermediate_result():
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    model.define_time_range(1., 1, 1, 2)

    make_basic_model_with_bus(model, True, 1., 0.)

    model.solve({SolverOption.INTERMEDIATE_RESULTS_PATH:"result.csv"})
    read_csv_file = pd.read_csv("result.csv")
    del read_csv_file["Unnamed: 0"]

    os.remove("result.csv")

    assert model._Eesrep__results.all().all() == read_csv_file.all().all()


@pytest.mark.Unit
@pytest.mark.solve
def test_intermediate_result_wrong_path():
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    model.define_time_range(1., 1, 1, 2)

    make_basic_model_with_bus(model, True, 1., 0.)

    try:
        model.solve({SolverOption.INTERMEDIATE_RESULTS_PATH:"/home/wdfzejgznerjgzenrg/result.csv"})
        assert False, "Intermediate result path leads to an unexisting file."
    except ValueError:
        assert True