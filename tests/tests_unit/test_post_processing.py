import math
from eesrep.eesrep_exceptions import PostProcessingException
import numpy as np
from os import environ
import pandas as pd
import pytest

import eesrep
from eesrep.components.converter import Converter
from eesrep.components.sink_source import FatalSink, Source

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

def make_basic_model(model:eesrep.Eesrep):
    source = Source("source", 0., 100., 1.)
    model.add_component(source)

    fatal_sink = FatalSink("load", pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]}))
    model.add_component(fatal_sink)

    model.add_link(source.power_out, fatal_sink.power_in, 1., 0.)

@pytest.mark.Unit
@pytest.mark.postpro
def test_post_processing_one_horizon():
    def post_pro(results:pd.DataFrame) -> pd.DataFrame:
        print(results.columns)
        results["source_power_out"] *= 2
        return results

    model = eesrep.Eesrep(solver=solver_for_tests)
    make_basic_model(model)

    model.set_post_processing(post_pro)
    model.define_time_range(1., 1, 5, 1)

    model.solve()

    results = model.get_results(as_dataframe=True)

    assert np.max(np.abs(results["source_power_out"].values - np.array([2, 4, 6, 8, 10]))) == 0, "Error in post-processing"

@pytest.mark.Unit
@pytest.mark.postpro
def test_post_processing_n_horizon():
    def post_pro(results:pd.DataFrame):
        print(results)
        results["source_power_out"] *= 2
        return results

    model = eesrep.Eesrep(solver=solver_for_tests)
    make_basic_model(model)

    model.set_post_processing(post_pro)
    model.define_time_range(1., 1, 1, 5)

    model.solve()

    results = model.get_results(as_dataframe=True)

    assert np.max(np.abs(results["source_power_out"].values - 
                         np.array([1*math.pow(2, 5), 2*math.pow(2, 4), 3*math.pow(2, 3), 4*math.pow(2, 2), 5*math.pow(2, 1)]))) == 0, \
        "Error in post-processing"
    
@pytest.mark.Unit
@pytest.mark.postpro
def test_two_post_processing_arguments():
    def post_pro(results:pd.DataFrame, step:int):
        return results

    model = eesrep.Eesrep(solver=solver_for_tests)
    make_basic_model(model)

    try:
        model.set_post_processing(post_pro)
        assert False, "Provided post-processing function is not valid, only one argument is acceptable."
    except AssertionError:
        assert True
    
@pytest.mark.Unit
@pytest.mark.postpro
def test_post_processing_change_column():
    def post_pro(results:pd.DataFrame):
        results.pop("time")
        return results

    model = eesrep.Eesrep(solver=solver_for_tests)
    make_basic_model(model)

    model.set_post_processing(post_pro)
    model.define_time_range(1., 1, 1, 5)

    try:
        model.solve()
        assert False, "A column was added to the dataframe during the post-processing."
    except PostProcessingException as e:
        assert True, f"Caught exception : {str(e)}"
    
@pytest.mark.Unit
@pytest.mark.postpro
def test_post_processing_change_line_count():
    def post_pro(results:pd.DataFrame):
        results = results.drop(0)
        return results

    model = eesrep.Eesrep(solver=solver_for_tests)
    make_basic_model(model)

    model.set_post_processing(post_pro)
    model.define_time_range(1., 1, 1, 5)

    try:
        model.solve()
        assert False, "A line was removed from the dataframe during the post-processing."
    except PostProcessingException as e:
        assert True, f"Caught exception : {str(e)}"
    
@pytest.mark.Unit
@pytest.mark.postpro
def test_post_processing_function_type():
    model = eesrep.Eesrep(solver=solver_for_tests)

    try:
        model.set_post_processing(2)
        assert False, "The post-processing function must be a callable."
    except TypeError as e:
        assert True, f"Caught exception : {str(e)}"
    
@pytest.mark.Unit
@pytest.mark.postpro
def test_post_processing_change_line_count():
    def post_pro(results:pd.DataFrame):
        return results
    
    model = eesrep.Eesrep(solver=solver_for_tests)
    model.set_post_processing(post_pro)

    try:
        model.set_post_processing(post_pro)
        assert False, "The post-processing function was defined twice."
    except RuntimeError as e:
        assert True, f"Caught exception : {str(e)}"