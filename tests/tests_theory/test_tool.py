from os import path, environ
import pandas as pd
import numpy as np

import pytest

from eesrep import Eesrep
from eesrep.components.sink_source import FatalSink, Sink, Source
from eesrep.components.tool import Delayer, GreaterThan, LowerThan, Integral

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "cplex"

@pytest.mark.Theory
@pytest.mark.Tool
@pytest.mark.Delayer
def test_tool_delayer():
    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    model.add_component(Source("source", 0., 100., 1.))
    model.add_component(Source("source2", 0., 100., 100.))

    model.add_component(Sink("sink", 0., 100., 1.))
    model.add_component(Delayer("delayer", 5, 42.))

    model.add_component (FatalSink("fatal_sink", pd.DataFrame({"time":list(range(30)), "value":list(range(30))})))

    model.create_bus("bus", {
                                "name":"bus"
                            })

    model.add_link("source", "power_out", "delayer", "power_in", 1., 0.)

    model.plug_to_bus("delayer", "power_out", "bus", True, 1., 0.)
    model.plug_to_bus("source2", "power_out", "bus", True, 1., 0.)
    model.plug_to_bus("sink", "power_in", "bus", False, 1., 0.)
    model.plug_to_bus("fatal_sink", "power_in", "bus", False, 1., 0.)

    model.define_time_range(1., 15, 15, 2)
    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert np.max(np.abs(results["delayer_power_out"].to_numpy()[0:5] - 42)) < 1e-5, "Past time not filled with default"
    assert np.max(np.abs(results["source_power_out"].to_numpy()[0:10] - results["delayer_power_out"].to_numpy()[5:15])) < 1e-5, "Offset not set right"
    assert np.max(np.abs(results["source_power_out"].to_numpy()[10:15] - results["delayer_power_out"].to_numpy()[15:20])) < 1e-5, "History not read right"

@pytest.mark.Theory
@pytest.mark.Tool
@pytest.mark.Integral
def test_tool_integral():
    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    model.add_component(Source("source", 0., 100., 1.))

    model.add_component(Integral("integral", 5))

    model.add_component (FatalSink("fatal_sink", pd.DataFrame({"time":list(range(30)), "value":list(range(30))})))

    model.add_link("source", "power_out", "fatal_sink", "power_in", 1., 0.)
    model.add_link("source", "power_out", "integral", "power_in", 1., 0.)

    model.define_time_range(1., 15, 15, 2)
    model.solve()

    results = model.get_results(as_dataframe=True)
    
    assert results["integral_power_out"].to_numpy()[0] == 1, "Past time not filled with default"
    assert np.max(np.abs(results["integral_power_out"].to_numpy() - results.loc[:, "source_power_out"].rolling(5, min_periods=1).sum())) < 1e-5, "Sum not done right"


@pytest.mark.Theory
@pytest.mark.Tool
@pytest.mark.GreaterThan
def test_tool_greater_than():
    """
        Tests the greater than component
    """
    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    model.create_bus("bus", {
                                "name":"bus_1"
                            })

    model.add_component(Source("source", 0., 10000., 1.))

    model.add_component(Sink("sink", 0., 10000., 0.01))

    model.add_component(GreaterThan("greater_than", 50.))

    model.add_component (FatalSink("fatal_sink_1", pd.DataFrame({"time":list(range(100)), "value":list(range(100))})))
    
    model.plug_to_bus("source", "power_out", "bus_1", True, 1., 0.)
    model.plug_to_bus("fatal_sink_1", "power_in", "bus_1", False, 1., 0.)
    model.plug_to_bus("sink", "power_in", "bus_1", False, 1., 0.)
    
    model.add_link("source", "power_out", "greater_than", "power_in", 1., 0.)

    model.define_time_range(1., 1, 100, 1)

    model.solve()

    results = model.get_results(as_dataframe=True)

    assert np.min(results["source_power_out"].to_numpy()) == 50, "Greater than constraint not working"


@pytest.mark.Theory
@pytest.mark.Tool
@pytest.mark.LowerThan
def test_tool_lower_than():
    """
        Tests the lower than component
    """
    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    model.create_bus("bus", {
                                "name":"bus_1"
                            })

    model.add_component(Source("source", 0., 10000., 1.))

    model.add_component(Source("back_up", 0., 10000., 100.))

    model.add_component(Sink("sink", 0., 10000., 0.01))

    model.add_component(LowerThan("lower_than", 50.))

    model.add_component (FatalSink("fatal_sink_1", pd.DataFrame({"time":list(range(100)), "value":list(range(100))})))
    
    model.plug_to_bus("source", "power_out", "bus_1", True, 1., 0.)
    model.plug_to_bus("back_up", "power_out", "bus_1", True, 1., 0.)
    model.plug_to_bus("fatal_sink_1", "power_in", "bus_1", False, 1., 0.)
    model.plug_to_bus("sink", "power_in", "bus_1", False, 1., 0.)
    
    model.add_link("source", "power_out", "lower_than", "power_in", 1., 0.)

    model.define_time_range(1., 1, 100, 1)

    model.solve()

    results = model.get_results(as_dataframe=True)
    print(results)
    assert np.max(results["source_power_out"].to_numpy()) == 50, "Lower than constraint not working"





if __name__ == '__main__':
    test_tool_delayer()
