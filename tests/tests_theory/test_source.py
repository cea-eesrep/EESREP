from os import path, environ
import pandas as pd
import numpy as np

from eesrep import Eesrep

import pytest

from eesrep.components.sink_source import FatalSink, Source

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "cplex"

@pytest.mark.Theory
@pytest.mark.SourceLoad
@pytest.mark.G_001
def test_G_001_production_price():
    app_home = path.dirname(path.realpath(__file__))

    reference_data = pd.read_csv(path.join(app_home, "DataSeries", "G_001_dataseries.csv"), sep=";")
    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    model.create_bus("bus", {
                                "name":"bus_1"
                            })

    model.add_component(Source("oil", 0., 100., 5.))
    model.add_component(Source("gas", 0., 100., 1.))

    model.add_component(FatalSink("load", (reference_data[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"})))

    model.plug_to_bus("oil", "power_out", "bus_1", False, 1., 0.)
    model.plug_to_bus("gas", "power_out", "bus_1", False, 1., 0.)
    model.plug_to_bus("load", "power_in", "bus_1", True, 1., 0.)

    model.define_time_range(3600., 1, 1000, 1)
    model.solve()

    results = model.get_results(as_dataframe=True)
    assert np.max(results["oil_power_out"].to_numpy() - np.maximum(results["load_power_in"].to_numpy() - 100, 0)) < 1e-5
    assert np.max(results["gas_power_out"].to_numpy() - np.minimum(results["load_power_in"].to_numpy(), 100.)) < 1e-5

if __name__ == '__main__':
    test_G_001_production_price()
