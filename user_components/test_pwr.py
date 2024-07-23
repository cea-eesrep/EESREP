import math
from os import environ, path

from eesrep.components.bus import GenericBus
import numpy as np
import pandas as pd
import pytest
from pwr import Pwr

from eesrep import Eesrep
from eesrep.components.sink_source import FatalSink, Sink, Source

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CPLEX"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "docplex"



@pytest.mark.Theory
@pytest.mark.PWR_001
def test_PWR_001():
    app_home = path.dirname(path.realpath(__file__))

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    time_df = pd.DataFrame([3600*i for i in range(1000)], columns=["Time"])
    load_df = pd.DataFrame([50 + 40 * math.sin(i/50) for i in range(1000)], columns=["Load"])
    data_ts = pd.concat([time_df, load_df], axis=1)

    import matplotlib.pyplot as plt

    bus = GenericBus("bus")
    model.add_component(bus)

    source = Source("source", 0., 10000., 1.)
    unsupplied = Source("unsupplied", 0., 10000., 10.)
    spilled = Sink("spilled", 0., 10000., 5000.)
    fatal_sink = FatalSink("fatal_sink", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))
    pwr = Pwr("pwr",
                                        efficiency=1.,
                                        p_min=30.,
                                        p_max=100.,
                                        init_efpd=0.,
                                        min_time_100=3,
                                        min_time_low=3,
                                        max_time_low=8,
                                        variable_rate=0.1,
                                        power_steps=7
                                )

    model.add_component(source)
    model.add_component(unsupplied)
    model.add_component(spilled)
    model.add_component(fatal_sink)
    model.add_component(pwr)


    model.add_link(source.power_out, pwr.power_in, 1., 0.)

    model.plug_to_bus(pwr.power_out, bus.input, 1., 0.)
    model.plug_to_bus(unsupplied.power_out, bus.input, 1., 0.)
    model.plug_to_bus(fatal_sink.power_in, bus.output, 1., 0.)
    model.plug_to_bus(spilled.power_in, bus.output, 1., 0.)

    model.define_time_range(3600., 100, 100, 10)

    model.solve()

    results = model.get_results(as_dataframe=True)

    plt.figure(figsize=(16,16))
    plt.subplot(311)
    plt.plot(results["pwr_power_out"], label = "PWR power out")
    plt.plot(results["pwr_power_main"], label = "PWR power main")
    plt.plot(results["pwr_power_variable"], label = "PWR power variable")
    plt.plot(data_ts["Load"], label = "Load", linestyle = "dashed")
    plt.xlim([0,20])
    plt.legend()
    plt.subplot(312)
    plt.plot(results["pwr_manoeuver"], label = "PWR manoeuver")
    plt.plot(results["pwr_power_step"], label = "PWR power_step")
    plt.plot(results["pwr_manoeuver_change_down"], label = "PWR manoeuver_change_down")
    plt.plot(results["pwr_manoeuver_change_up"], label = "PWR manoeuver_change_up")
    plt.plot(results["pwr_manoeuver_count"], label = "PWR manoeuver_count")
    plt.xlim([0,20])
    plt.legend()
    plt.subplot(313)
    plt.plot(results["spilled_power_in"], label = "Spilled")
    plt.plot(results["unsupplied_power_out"], label = "Unsupplied")
    plt.xlim([0,20])
    plt.legend()
    plt.show()
    #   Relaxed condition as significative figures is too low.
    # assert min(np.array(results["pwr_storage"]) - np.array((500000.*data_ts["Stockage_Min"]).iloc[1:-1])) >= -1e-5




if __name__ == "__main__":
    test_PWR_001()