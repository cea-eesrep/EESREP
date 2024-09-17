import eesrep
from eesrep.components.generic_component import GenericComponent
from eesrep.components.sink_source import FatalSink, Source
from eesrep.eesrep_enum import TimeSerieType
from eesrep.eesrep_io import ComponentIO
from eesrep.solver_interface.generic_interface import GenericInterface

import numpy as np
import pandas as pd
import pytest

class FakeFutureComponent(GenericComponent):
    def __init__(self, name:str):
        self.name = name

        self.time_series = {}

        self.intensive_var_in = ComponentIO(self.name, "intensive_var_in", TimeSerieType.INTENSIVE, True)
        self.intensive_var_out = ComponentIO(self.name, "intensive_var_out", TimeSerieType.INTENSIVE, True)
        self.intensive_var_out_save = ComponentIO(self.name, "intensive_var_out_save", TimeSerieType.INTENSIVE, False)
        self.extensive_var = ComponentIO(self.name, "extensive_var", TimeSerieType.EXTENSIVE, True)
        self.extensive_var_save = ComponentIO(self.name, "extensive_var_save", TimeSerieType.EXTENSIVE, False)

    def io_from_parameters(self) -> dict:
        return { 
                    "intensive_var_in": self.intensive_var_in,
                    "intensive_var_out": self.intensive_var_out,
                    "intensive_var_out_save": self.intensive_var_out_save,
                    "extensive_var": self.extensive_var,
                    "extensive_var_save": self.extensive_var_save
                }

    def build_model(self,
        component_name:str,
        time_steps:list,
        time_series:pd.DataFrame,
        history:pd.DataFrame,
        model_interface:GenericInterface, 
        future:pd.DataFrame):

        print(time_steps)
        print("FUTUUUURE", future)

        objective = 0.
        variables = {}

        variables["intensive_var_in"] = model_interface.get_new_continuous_variable_list(component_name+"_intensive_var_in_", len(time_steps), None, None)
        variables["intensive_var_out"] = model_interface.get_new_continuous_variable_list(component_name+"_intensive_var_out_", len(time_steps), None, None)
        variables["intensive_var_out_save"] = model_interface.get_new_continuous_variable_list(component_name+"_intensive_var_out_save_", len(time_steps), None, None)
        variables["extensive_var"] = model_interface.get_new_continuous_variable_list(component_name+"_extensive_var_", len(time_steps), None, None)
        variables["extensive_var_save"] = model_interface.get_new_continuous_variable_list(component_name+"_extensive_var_save_", len(time_steps), None, None)

        for i in range(len(time_steps)):
            model_interface.add_equality(model_interface.sum_variables([variables["intensive_var_out"][i], -variables["intensive_var_in"][i]]), 0)

            if i < len(future):
                model_interface.add_equality(model_interface.sum_variables([future["extensive_var"][i], -variables["extensive_var_save"][i]]), 0)
                model_interface.add_equality(model_interface.sum_variables([future["intensive_var_out"][i], -variables["intensive_var_out_save"][i]]), 0)

            if i == 0 and len(history) == 0:
                model_interface.add_equality(model_interface.sum_variables([variables["extensive_var"][i], -variables["intensive_var_in"][i]*time_steps[i]]), 0)
            elif i == 0:
                model_interface.add_equality(model_interface.sum_variables([variables["extensive_var"][i], -variables["intensive_var_in"][i]*time_steps[i], -history.loc[len(history)-1, "extensive_var"]]), 0)
            else:
                model_interface.add_equality(model_interface.sum_variables([variables["extensive_var"][i], -variables["intensive_var_in"][i]*time_steps[i], -variables["extensive_var"][i-1]]), 0)
            
        return variables, objective

def make_model():
    model = eesrep.Eesrep()

    source = Source("source", 0., 100., 1.)
    model.add_component(source)

    load = FatalSink("load", pd.DataFrame({"time":list(range(10)), "value":list(range(10))}))
    model.add_component(load)

    ftc = FakeFutureComponent("ftc")
    model.add_component(ftc)

    model.add_link(source.power_out, ftc.intensive_var_in, 1., 0.)
    model.add_link(ftc.intensive_var_out, load.power_in, 1., 0.)
    
    return model

@pytest.mark.Unit
@pytest.mark.future
def test_future_intensive_constant_time_step():
    model = make_model()

    model.define_time_range(time_step = 1., 
                                time_shift = 1, 
                                future_size = 3, 
                                horizon_count = 2)
    model.solve()

    res = model.get_results(as_dataframe=True)

    assert np.max(np.abs(np.array(res["ftc_intensive_var_out"])[1:-1] - np.array(res["ftc_intensive_var_out_save"])[1:-1])) == 0., "Content of history wrong."
    assert res.loc[0, "ftc_intensive_var_out_save"] == 0., "Future of first horizon was not filled with 0."
    assert res.loc[len(res)-1, "ftc_intensive_var_out_save"] == 0., "Future was not extrapolated with nan"

@pytest.mark.Unit
@pytest.mark.future
def test_future_extensive_constant_time_step():
    model = make_model()

    model.define_time_range(time_step = 1., 
                                time_shift = 1, 
                                future_size = 3, 
                                horizon_count = 2)
    model.solve()

    res = model.get_results(as_dataframe=True)

    assert np.max(np.abs(np.array(res["ftc_extensive_var"])[1:-1] - np.array(res["ftc_extensive_var_save"])[1:-1])) == 0., "Content of history wrong."
    assert res.loc[0, "ftc_extensive_var_save"] == 0., "Future of first horizon was not filled with 0."
    assert res.loc[len(res)-1, "ftc_extensive_var_save"] == 0., "Future was not extrapolated with nan"


@pytest.mark.Unit
@pytest.mark.future
def test_future_intensive_variable_time_step():
    model = make_model()

    model.define_time_range(time_step = 1., 
                                time_shift = 1, 
                                future_size = 3, 
                                horizon_count = 3)
    
    model.set_custom_steps([1, 2, 3])
    model.solve()

    res = model.get_results(as_dataframe=True)

    print(pd.DataFrame({"time":res["time"], "val_int":res["ftc_intensive_var_out"], "save_int":res["ftc_intensive_var_out_save"]}))

    assert np.max(np.abs(np.array([2.5, 3.5, 4.75]) - np.array(res["ftc_intensive_var_out_save"])[1:-1])) == 0., "Content of history wrong."
    assert res.loc[0, "ftc_intensive_var_out_save"] == 0., "Future of first horizon was not filled with 0."
    assert res.loc[len(res)-1, "ftc_intensive_var_out_save"] == 0., "Future was not extrapolated with nan"

@pytest.mark.Unit
@pytest.mark.future
def test_future_extensive_variable_time_step():
    model = make_model()

    model.define_time_range(time_step = 1., 
                                time_shift = 1, 
                                future_size = 3, 
                                horizon_count = 4)
    
    model.set_custom_steps([1, 2, 3])
    model.solve()

    res = model.get_results(as_dataframe=True)

    print(res)

    print(res["ftc_extensive_var"])
    print(res["ftc_extensive_var_save"])

    assert np.max(np.abs(np.array([6, 10, 15, 51]) - np.array(res["ftc_extensive_var_save"])[1:-1])) == 0., "Content of history wrong."
    assert res.loc[0, "ftc_extensive_var_save"] == 0., "Future of first horizon was not filled with 0."
    assert res.loc[len(res)-1, "ftc_extensive_var_save"] == 0., "Future was not extrapolated with nan"
