
from os import environ
import pytest

import pandas as pd
import numpy as np

import eesrep
from eesrep.eesrep_exceptions import ComponentNameException, ParametersException, TimeSerieException
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_enum import TimeSerieType
from eesrep.components.generic_component import GenericComponent

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "cplex"


class FakeComponent(GenericComponent):
    def __init__(self, name:str, intensive_ts:pd.DataFrame, extensive_ts:pd.DataFrame = pd.DataFrame()):
        self.name = name

        self.time_series = {}
        self.time_series["intensive_ts"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": intensive_ts
                                            }
                                            
        if not extensive_ts.empty:
            self.time_series["extensive_ts"]={
                                                    "type": TimeSerieType.EXTENSIVE,
                                                    "value": extensive_ts
                                                }
    def io_from_parameters(self) -> dict:
        return { 
                    "intensive_var":{
                                        "type": TimeSerieType.INTENSIVE,
                                        "continuity": False
                                    },
                    "extensive_var":{
                                        "type": TimeSerieType.EXTENSIVE,
                                        "continuity": False
                                    }
                }

    def build_model(self,
        component_name:str,
        time_steps:list,
        time_series:pd.DataFrame,
        history:pd.DataFrame,
        model_interface:GenericInterface):
        pass

def make_ts_dict():
    return pd.DataFrame([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6]], columns=["time", "value"])

@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_intensive_ts():
    """
        Tests the function is_it_intensive
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)
    
    assert model._Eesrep__is_it_intensive("fake", "intensive_ts"), "intensive_ts should be considered as intensive"
    assert not model._Eesrep__is_it_intensive("fake", "extensive_ts"), "extensive_ts should not be considered as intensive"
    
@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_extensive_ts():
    """
        Tests the function is_it_extensive for time series
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)
    
    assert model._Eesrep__is_it_extensive("fake", "extensive_ts"), "extensive_ts should be considered as extensive"
    assert not model._Eesrep__is_it_extensive("fake", "intensive_ts"), "intensive_ts should not be considered as extensive"

    
@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_intensive_io():
    """
        Tests the function is_it_intensive for input_output
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict())
    model.add_component(fc)
    
    assert model._Eesrep__is_it_intensive("fake", "intensive_var"), "intensive_var should be considered as intensive"
    assert not model._Eesrep__is_it_intensive("fake", "extensive_var"), "extensive_var should not be considered as intensive"
    
@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_extensive_io():
    """
        Tests the function is_it_extensive for input_output
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict())
    model.add_component(fc)
    
    assert model._Eesrep__is_it_extensive("fake", "extensive_var"), "extensive_var should be considered as extensive"
    assert not model._Eesrep__is_it_extensive("fake", "intensive_var"), "intensive_var should not be considered as extensive"
    
@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_intensive_wrong_component():
    """
        Tests the function is_it_intensive with invalid component
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model._Eesrep__is_it_intensive("fake", "intensive_var")
        assert False, "Given component does not exist"
    except ComponentNameException:
        assert True

@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_extensive_wrong_component():
    """
        Tests the function is_it_extensive with invalid component
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model._Eesrep__is_it_extensive("fake", "intensive_var")
        assert False, "Given component does not exist"
    except ComponentNameException:
        assert True

@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_intensive_wrong_serie_name():
    """
        Tests the function is_it_intensive with invalid key
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)
    
    try:
        model._Eesrep__is_it_intensive("fake", "some_serie")
        assert False, "Given serie does not exist"
    except TimeSerieException:
        assert True

@pytest.mark.Unit
@pytest.mark.timeseries
def test_is_it_extensive_wrong_serie_name():
    """
        Tests the function is_it_extensive with invalid key
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)
    
    try:
        model._Eesrep__is_it_extensive("fake", "some_serie")
        assert False, "Given serie does not exist"
    except TimeSerieException:
        assert True

        
@pytest.mark.Unit
@pytest.mark.timeseries
def test_setting_wrong_ts_keys():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    ts = pd.DataFrame([0, 1, 2, 3, 4, 5, 6], columns=["value"])
    fc = FakeComponent("fake", ts)

    try:
        model.add_component(fc)
        assert False, "Serie given does not respect the required columns names"
    except KeyError:
        assert True
        
@pytest.mark.Unit
@pytest.mark.timeseries
def test_setting_wrong_ts_keys_2():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    ts = pd.DataFrame([0, 1, 2, 3, 4, 5, 6], columns=["time"])
    fc = FakeComponent("fake", ts)

    try:
        model.add_component(fc)
        assert False, "Serie given does not respect the required columns names"
    except KeyError:
        assert True
        
@pytest.mark.Unit
@pytest.mark.timeseries
def test_setting_timeserie():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)

    assert model._Eesrep__time_series["fake_intensive_ts"].all() == make_ts_dict()["value"].all()
    
@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_integration():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)

    model._Eesrep__make_ts_integrated_column("fake_intensive_ts")

    assert np.max(np.abs(model._Eesrep__time_series["integrated_fake_intensive_ts"].values - np.array([0, 1, 3, 6, 10, 15, 21]))) == 0

@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_integration_wrong_columns():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model._Eesrep__make_ts_integrated_column("fake_intensive_ts")
        assert False, "Provided column does not exist"
    except KeyError:
        assert True

@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_wrong_extract_context():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)

    model._Eesrep__make_ts_integrated_column("fake_intensive_ts")

    try:
        model._Eesrep__get_time_serie_extract("fake")
        assert False, "Shouldn't extract time series before defining time steps."
    except RuntimeError:
        assert True

@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_wrong_component_extract():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)
    model.define_time_range(0.5, 1, 10, 1)

    try:
        model._Eesrep__get_time_serie_extract("wrong_component")
        assert False, "Given component doesn't exist."
    except ComponentNameException:
        assert True


@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_interpolation():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)
    model.define_time_range(0.5, 1, 10, 1)

    model._Eesrep__make_ts_integrated_column("fake_intensive_ts")
    model._Eesrep__make_ts_integrated_column("fake_extensive_ts")

    assert np.max(np.abs(model._Eesrep__interpolate(model._Eesrep__time_series, model._Eesrep__make_time_steps(), "integrated_fake_intensive_ts") 
                            - [0., 0.5, 1., 2., 3., 4.5, 6., 8., 10., 12.5, 15.])) == 0
    assert np.max(np.abs(model._Eesrep__interpolate(model._Eesrep__time_series, model._Eesrep__make_time_steps(), "integrated_fake_extensive_ts") 
                            - [0., 0.5, 1., 2., 3., 4.5, 6., 8., 10., 12.5, 15.])) == 0
        
@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_make_time_series_extract():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)

    model.define_time_range(0.5, 1, 10, 1)
    extract = model._Eesrep__get_time_serie_extract("fake")
    
    assert np.max(np.abs(extract["intensive_ts"] - [1, 1, 2, 2, 3, 3, 4, 4, 5, 5])) == 0
    assert np.max(np.abs(extract["extensive_ts"] - [0.5, 0.5, 1. , 1. , 1.5, 1.5, 2. , 2. , 2.5, 2.5])) == 0

    
@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_set_different_time_series_time_column():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)

    assert np.max(np.abs(model._Eesrep__time_series["time"].values - make_ts_dict()["time"].values)) == 0
    assert np.max(np.abs(model._Eesrep__time_series["fake_intensive_ts"].values - make_ts_dict()["value"].values)) == 0

    model._Eesrep__add_time_serie("extensive_ts", pd.DataFrame([[0, 0], [3, 3], [7, 7]], columns=["time", "value"]))

    model._Eesrep__interpolate_time_series()

    assert np.max(np.abs(model._Eesrep__time_series["fake_intensive_ts"].values - np.array([0, 1, 2, 3, 4, 5, 6, 6]))) == 0
    assert np.max(np.abs(model._Eesrep__time_series["extensive_ts"].values - np.array([0, 1, 2, 3, 4, 5, 6, 7]))) == 0


@pytest.mark.Unit
@pytest.mark.timeseries
def test_interpolate_without_time():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model._Eesrep__interpolate(pd.DataFrame([[0, 0], [1, 1]], columns=["value", "value2"]),
                                        [0, 0], 
                                        "value")
        assert False, "The dataframe doesn't have the given column."
    except KeyError:
        assert True
        

@pytest.mark.Unit
@pytest.mark.timeseries
def test_interpolate_wrong_column():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model._Eesrep__interpolate(make_ts_dict(), [0, 0], "wrong_column")
        assert False, "The dataframe doesn't have the given column."
    except KeyError:
        assert True