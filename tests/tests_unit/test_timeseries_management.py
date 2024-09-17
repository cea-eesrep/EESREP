
from math import isnan
from os import environ
from eesrep.eesrep_io import ComponentIO
import pytest

import pandas as pd
import numpy as np

import eesrep
from eesrep.eesrep_exceptions import ComponentNameException, ParametersException, TimeSerieException, UndefinedTimeRangeException
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_enum import TimeSerieType
from eesrep.components.generic_component import GenericComponent
from eesrep.test_interface_solver import get_couple_from_key

solver_for_tests, interface_for_tests = get_couple_from_key()


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
        model_interface:GenericInterface,
        future:pd.DataFrame = None):
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

    assert model._Eesrep__time_serie_manager._TimeSerieManager__time_series["fake_intensive_ts"].all() == make_ts_dict()["value"].all()
    
@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_integration():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)

    model._Eesrep__time_serie_manager._TimeSerieManager__make_ts_integrated_column("fake_intensive_ts")

    assert np.max(np.abs(model._Eesrep__time_serie_manager._TimeSerieManager__time_series["integrated_fake_intensive_ts"].values - np.array([0, 1, 3, 6, 10, 15, 21]))) == 0

@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_integration_wrong_columns():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model._Eesrep__time_serie_manager._TimeSerieManager__make_ts_integrated_column("fake_intensive_ts")
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

    model._Eesrep__time_serie_manager._TimeSerieManager__make_ts_integrated_column("fake_intensive_ts")

    try:
        model._Eesrep__time_serie_manager.get_time_serie_extract(model._Eesrep__make_time_steps(), fc)
        assert False, "Shouldn't extract time series before defining time steps."
    except UndefinedTimeRangeException:
        assert True

@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_wrong_time_serie_name():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    fc2 = FakeComponent("fake2", make_ts_dict(), extensive_ts = make_ts_dict())

    model.add_component(fc)
    model.define_time_range(0.5, 1, 10, 1)

    try:
        model._Eesrep__time_serie_manager.get_time_serie_extract(model._Eesrep__make_time_steps(), fc2)
        assert False, "Given component doesn't exist."
    except KeyError:
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

    model._Eesrep__time_serie_manager._TimeSerieManager__make_ts_integrated_column("fake_intensive_ts")
    model._Eesrep__time_serie_manager._TimeSerieManager__make_ts_integrated_column("fake_extensive_ts")

    assert np.max(np.abs(model._Eesrep__time_serie_manager.interpolate(model._Eesrep__make_time_steps(), "integrated_fake_intensive_ts") 
                            - [0., 0.5, 1., 2., 3., 4.5, 6., 8., 10., 12.5, 15.])) == 0
    assert np.max(np.abs(model._Eesrep__time_serie_manager.interpolate(model._Eesrep__make_time_steps(), "integrated_fake_extensive_ts") 
                            - [0., 0.5, 1., 2., 3., 4.5, 6., 8., 10., 12.5, 15.])) == 0
    

@pytest.mark.Unit
@pytest.mark.timeseries
def test_timeserie_interpolation_extrapolate_nan():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    fc = FakeComponent("fake", make_ts_dict(), extensive_ts = make_ts_dict())
    model.add_component(fc)
    model.define_time_range(0.5, 1, 4, 1)

    model._Eesrep__time_serie_manager._TimeSerieManager__make_ts_integrated_column("fake_intensive_ts")
    model._Eesrep__time_serie_manager._TimeSerieManager__make_ts_integrated_column("fake_extensive_ts")

    steps = [i+5 for i in model._Eesrep__make_time_steps()]

    assert list(model._Eesrep__time_serie_manager.interpolate(steps, "fake_intensive_ts", extrapolate_with_nan = True))[:3] == [5. , 5.5, 6.], "Time serie interpolation didn't return the right value"
    assert list(model._Eesrep__time_serie_manager.interpolate(steps, "fake_extensive_ts", extrapolate_with_nan = True))[:3] == [5. , 5.5, 6.], "Time serie interpolation didn't return the right value"

    assert isnan(model._Eesrep__time_serie_manager.interpolate(steps, "fake_intensive_ts", extrapolate_with_nan = True)[3]), "Time serie extrapolation didn't return Nan"
    assert isnan(model._Eesrep__time_serie_manager.interpolate(steps, "fake_intensive_ts", extrapolate_with_nan = True)[4]), "Time serie extrapolation didn't return Nan"
    assert isnan(model._Eesrep__time_serie_manager.interpolate(steps, "fake_extensive_ts", extrapolate_with_nan = True)[3]), "Time serie extrapolation didn't return Nan"
    assert isnan(model._Eesrep__time_serie_manager.interpolate(steps, "fake_extensive_ts", extrapolate_with_nan = True)[4]), "Time serie extrapolation didn't return Nan"

        
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
    extract = model._Eesrep__time_serie_manager.get_time_serie_extract(model._Eesrep__make_time_steps(), fc)
    
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

    assert np.max(np.abs(model._Eesrep__time_serie_manager._TimeSerieManager__time_series["time"].values - make_ts_dict()["time"].values)) == 0
    assert np.max(np.abs(model._Eesrep__time_serie_manager._TimeSerieManager__time_series["fake_intensive_ts"].values - make_ts_dict()["value"].values)) == 0

    model._Eesrep__time_serie_manager.add_time_serie("extensive_ts", pd.DataFrame([[0, 0], [3, 3], [7, 7]], columns=["time", "value"]), False)

    model._Eesrep__time_serie_manager.interpolate_time_series()

    assert np.max(np.abs(model._Eesrep__time_serie_manager._TimeSerieManager__time_series["fake_intensive_ts"].values - np.array([0, 1, 2, 3, 4, 5, 6, 6]))) == 0
    assert np.max(np.abs(model._Eesrep__time_serie_manager._TimeSerieManager__time_series["extensive_ts"].values - np.array([0, 1, 2, 3, 4, 5, 6, 7]))) == 0


@pytest.mark.Unit
@pytest.mark.timeseries
def test_interpolate_without_time():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    try:
        model._Eesrep__time_serie_manager.interpolate(pd.DataFrame([[0, 0], [1, 1]], columns=["value", "value2"]),
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
        model._Eesrep__time_serie_manager.interpolate(make_ts_dict(), [0, 0], "wrong_column")
        assert False, "The dataframe doesn't have the given column."
    except KeyError:
        assert True