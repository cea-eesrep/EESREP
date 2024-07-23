"""
    Cluster component tests
"""
from os import path, environ
import pandas as pd
from eesrep.components.bus import GenericBus
import numpy as np

from eesrep import Eesrep

import pytest
from eesrep.components.converter import Cluster

from eesrep.components.sink_source import FatalSink, Sink, Source
from eesrep.test_interface_solver import get_couple_from_key

solver_for_tests, interface_for_tests = get_couple_from_key()

@pytest.mark.Theory
@pytest.mark.Cluster
@pytest.mark.C_001
def test_C_001_start_necessary():
    """
        Tests if the cluster starts the right amount of machines
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "DataSeries", "C_001_dataseries.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    bus = GenericBus("bus")
    model.add_component(bus)

    source = Source("source", 0., 10000., 1.)
    sink = Sink("sink", 0., 10000., 10.)
    cluster = Cluster("cluster", 1., 1., 100, 10, 1, 1, 10.)
    fatal_sink = FatalSink("fatal_sink", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))

    model.add_component(source)
    model.add_component(sink)
    model.add_component(cluster)
    model.add_component(fatal_sink)

    model.add_link(source.power_out, cluster.power_in, 1., 0.)
    model.add_link(cluster.n_machine, sink.power_in, 1., 0.)

    model.plug_to_bus(cluster.power_out, bus.input, 1., 0.)

    model.plug_to_bus(fatal_sink.power_in, bus.output, 1., 0.)

    model.define_time_range(3600., 100, 100, 10)

    model.solve()

    results = model.get_results(as_dataframe=True)
    
    criterion_array = np.array(results["cluster_n_machine"]) - np.ceil(np.array(data_ts["Load"].iloc[1:1001]/100.))
    assert max(criterion_array) == 0, criterion_array











@pytest.mark.Theory
@pytest.mark.Cluster
@pytest.mark.C_002
def test_C_002_p_min():
    """
        Tests if the cluster minimal power works
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "DataSeries", "C_002_dataseries.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    bus = GenericBus("bus")
    model.add_component(bus)

    source = Source("source", 0., 10000., 1.)
    sink = Sink("sink", 0., 10000., 10.)
    cluster = Cluster("cluster", 1., 60., 100, 2, 1, 1, 1.)
    fatal_sink = FatalSink("fatal_sink", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))
    
    model.add_component(source)
    model.add_component(sink)
    model.add_component(cluster)
    model.add_component(fatal_sink)

    model.add_link(source.power_out, cluster.power_in, 1., 0.)

    model.plug_to_bus(cluster.power_out, bus.input, 1., 0.)

    model.plug_to_bus(fatal_sink.power_in, bus.output, 1., 0.)
    model.plug_to_bus(sink.power_in, bus.output, 1., 0.)

    model.define_time_range(3600., 100, 100, 10)

    model.solve()

    results = model.get_results(as_dataframe=True)
    
    reference = np.where(np.array(data_ts["Load"].iloc[1:1001]) > np.ceil(np.array(data_ts["Load"].iloc[1:1001]/100.))*60,
                            np.array(data_ts["Load"].iloc[1:1001]),
                            np.ceil(np.array(data_ts["Load"].iloc[1:1001]/100.))*60)

    criterion_array = reference - np.array(results["cluster_power_out"])

    assert max(criterion_array) < 1e-5, criterion_array









@pytest.mark.Theory
@pytest.mark.Cluster
@pytest.mark.C_003
def test_C_003_stop_necessary():
    """
        Tests if the cluster turns off unused machines
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "DataSeries", "C_003_dataseries.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    bus = GenericBus("bus")
    model.add_component(bus)

    source = Source("source", 0., 10000., 1.)
    sink = Sink("sink", 0., 10000., 20.)
    sink_n_machine = Sink("sink_n_machine", 0., 10000., 20.)
    cluster = Cluster("cluster", 1., 60., 100, 8, 1, 1, 0.)
    fatal_sink = FatalSink("fatal_sink", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))
    
    model.add_component(source)
    model.add_component(sink)
    model.add_component(sink_n_machine)
    model.add_component(cluster)
    model.add_component(fatal_sink)

    model.add_link(source.power_out, cluster.power_in, 1., 0.)
    model.add_link(cluster.n_machine, sink_n_machine.power_in, 1., 0.)

    model.plug_to_bus(cluster.power_out, bus.input, 1., 0.)

    model.plug_to_bus(fatal_sink.power_in, bus.output, 1., 0.)
    model.plug_to_bus(sink.power_in, bus.output, 1., 0.)

    model.define_time_range(3600., 200, 200, 5)

    model.solve()

    results = model.get_results(as_dataframe=True)

    assert np.max(np.ceil(results["cluster_power_out"]/100) - np.array(results["cluster_n_machine"])) < 1










@pytest.mark.Theory
@pytest.mark.Cluster
@pytest.mark.C_004
def test_C_004_min_time():
    """
        Tests the cluster machines minimal working time
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "DataSeries", "C_004_dataseries.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    bus = GenericBus("bus")
    model.add_component(bus)

    source = Source("source", 0., 10000., 20.)
    unsupplied = Source("unsupplied", 0., 10000., 5000.)
    sink = Sink("sink", 0., 10000., 500.)
    sink_n_machine = Sink("sink_n_machine", 0., 10000., 20.)
    cluster = Cluster("cluster", 1., 100., 100, 3, 6, 1, 0.)
    fatal_sink = FatalSink("fatal_sink", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))
    
    model.add_component(source)
    model.add_component(unsupplied)
    model.add_component(sink)
    model.add_component(sink_n_machine)
    model.add_component(cluster)
    model.add_component(fatal_sink)
    
    model.add_link(source.power_out, cluster.power_in, 1., 0.)

    model.plug_to_bus(cluster.power_out, bus.input, 1., 0.)
    model.plug_to_bus(unsupplied.power_out, bus.input, 1., 0.)
    model.plug_to_bus(fatal_sink.power_in, bus.output, 1., 0.)
    model.plug_to_bus(sink.power_in, bus.output, 1., 0.)

    model.define_time_range(3600., 200, 200, 5)

    model.solve()

    results = model.get_results(as_dataframe=True)

    assert max(np.where(results["fatal_sink_power_in"]>0,
                            results["cluster_n_machine"].rolling(15, center=True).sum() - 6*np.ceil(results["fatal_sink_power_in"]/100),
                            0)) == 0




 
@pytest.mark.Theory
@pytest.mark.Cluster
@pytest.mark.C_005
def test_C_005_min_off_time():
    """
        Tests the cluster machines minimal turn off time
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "DataSeries", "C_005_dataseries.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    bus = GenericBus("bus")
    model.add_component(bus)

    source = Source("source", 0., 10000., 1.)
    unsupplied = Source("unsupplied", 0., 10000., 10.)
    spilled= Sink("spilled", 0., 10000., 5000.)
    sink = Sink("sink", 0., 10000., 500.)
    sink_n_machine = Sink("sink_n_machine", 0., 10000., 20.)
    cluster = Cluster("cluster", 1., 100., 100, 2, 1, 6, 50.)
    fatal_sink = FatalSink("fatal_sink", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))
    
    model.add_component(source)
    model.add_component(unsupplied)
    model.add_component(spilled)
    model.add_component(sink)
    model.add_component(sink_n_machine)
    model.add_component(cluster)
    model.add_component(fatal_sink)

    model.add_link(source.power_out, cluster.power_in, 1., 0.)

    model.plug_to_bus(cluster.power_out, bus.input, 1., 0.)

    model.plug_to_bus(unsupplied.power_out, bus.input, 1., 0.)

    model.plug_to_bus(fatal_sink.power_in, bus.output, 1., 0.)
    model.plug_to_bus(spilled.power_in, bus.output, 1., 0.)

    model.define_time_range(3600., 100, 100, 10)

    model.solve()

    results = model.get_results(as_dataframe=True)

    assert max(np.where(results["fatal_sink_power_in"]==0,
                            (2-results["cluster_n_machine"]).rolling(15, center=True).sum() - 6*np.ceil((200-results["fatal_sink_power_in"])/100),
                            0)) == 0




if __name__ == "__main__":
    test_C_002_p_min()