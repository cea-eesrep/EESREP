"""Neural network pytest tests"""
from os import path, environ
import pandas as pd

import pytest

from eesrep import Eesrep
from eesrep.components.sink_source import FatalSource, Sink
from eesrep.eesrep_enum import SolverOption

from neural_network import NeuralNetwork

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "docplex"

@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_1_1
def test_nn_1_1():
    """
        Testing a 1 input, 1 output, zero deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_1_1.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))

    neural_network = NeuralNetwork("neural_network", 1, 1, 10000000., 
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_1_1.csv"))
    
    sink = Sink("sink", -10000000., 10000000., 1.)

    model.add_component(source)
    model.add_component(neural_network)
    model.add_component(sink)
    
    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)

    model.define_time_range(3600., 300, 200, 2)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_1_1_theory.csv"), sep = ",")
    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5



@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_2_1
def test_nn_2_1():
    """
        Testing a 2 inputs, 1 output, zero deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_2_1.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Input_0"]]).rename(columns={"Time":"time", "Input_0":"value"}))
                                    
    source_2 = FatalSource("source_2", (data_ts[["Time", "Input_1"]]).rename(columns={"Time":"time", "Input_1":"value"}))

    neural_network = NeuralNetwork("neural_network", 2, 1, 10.,
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_2_1.csv"))
    
    sink = Sink("sink", -10000000., 10000000., 1.)
    
    model.add_component(source)
    model.add_component(source_2)
    model.add_component(neural_network)
    model.add_component(sink)   

    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(source_2.power_out, neural_network.input_1, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)

    model.define_time_range(3600., 100, 100, 3)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_2_1_theory.csv"), sep = ",")
    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5

@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_1_2
def test_nn_1_2():
    """
        Testing a 1 input, 2 outputs, zero deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_1_2.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Input_0"]]).rename(columns={"Time":"time", "Input_0":"value"}))

    neural_network = NeuralNetwork("neural_network", 1,2,10.,
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_1_2.csv"))
    
    sink = Sink("sink", -10000000., 10000000., 1.)

    sink_2 = Sink("sink_2", -10000000., 10000000., 1.)
    
    model.add_component(source)
    model.add_component(neural_network)
    model.add_component(sink)    
    model.add_component(sink_2)
    
    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)
    model.add_link(neural_network.output_1, sink_2.power_in, 1., 0.)

    model.define_time_range(3600., 100, 100, 3)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_1_2_theory.csv"), sep = ",")
    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Output_1"] - results["neural_network_output_1"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5

@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_2_2
def test_nn_2_2():
    """
        Testing a 2 inputs, 2 outputs, zero deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_2_2.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Input_0"]]).rename(columns={"Time":"time", "Input_0":"value"}))

    source_2 = FatalSource("source_2", (data_ts[["Time", "Input_1"]]).rename(columns={"Time":"time", "Input_1":"value"}))

    neural_network = NeuralNetwork("neural_network", 2,2,10.,
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_2_2.csv"))

    sink = Sink("sink", -10000000., 10000000., 1.)
    sink_2 = Sink("sink_2", -10000000., 10000000., 1.)
    
    model.add_component(source)
    model.add_component(source_2)
    model.add_component(neural_network)
    model.add_component(sink)    
    model.add_component(sink_2)
    
    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(source_2.power_out, neural_network.input_1, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)
    model.add_link(neural_network.output_1, sink_2.power_in, 1., 0.)

    model.define_time_range(3600., 100, 100, 3)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_2_2_theory.csv"), sep = ",")
    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5


@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_1_15_15_1
def test_nn_1_15_15_1():
    """
        Testing a 1 input, 1 output, 2 layers of 15 neurons deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_1_15_15_1.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))

    neural_network = NeuralNetwork("neural_network", 1, 1, 1000000.,
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_1_15_15_1.csv"))

    sink = Sink("sink", -10000000., 10000000., 1.)
    
    model.add_component(source)
    model.add_component(neural_network)
    model.add_component(sink)    

    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)

    model.define_time_range(3600., 10, 10, 30)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_1_15_15_1_theory.csv"), sep = ",")

    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5

@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_1_5_5_1
def test_nn_1_5_5_1():
    """
        Testing a 1 input, 1 output, 2 layers of 5 neurons deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_1_5_5_1.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))

    neural_network = NeuralNetwork("neural_network", 1, 1, 10000000., 
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_1_5_5_1.csv"))

    sink = Sink("sink", -10000000., 10000000., 1.)
    
    model.add_component(source)
    model.add_component(neural_network)
    model.add_component(sink)    

    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)

    model.define_time_range(3600., 100, 100, 3)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_1_5_5_1_theory.csv"), sep = ",")

    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5


@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_1_5_5_5_5_5_5_1
def test_nn_1_5_5_5_5_5_5_1():
    """
        Testing a 1 input, 1 output, 6 layers of 5 neurons deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_1_5_5_5_5_5_5_1.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Load"]]).rename(columns={"Time":"time", "Load":"value"}))

    neural_network = NeuralNetwork("neural_network", 1, 1, 10000000., 
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_1_5_5_5_5_5_5_1.csv"))

    sink = Sink("sink", -10000000., 10000000., 1.)
    
    model.add_component(source)
    model.add_component(neural_network)
    model.add_component(sink)    

    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)

    model.define_time_range(3600., 10, 10, 30)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_1_5_5_5_5_5_5_1_theory.csv"), sep = ",")
    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5


@pytest.mark.Theory
@pytest.mark.NeuralNetwork
@pytest.mark.NN_2_5_5_5_2
def test_nn_2_5_5_5_2():
    """
        Testing a 2 inputs, 2 outputs, 3 layers of 15 neurons deep neural network.
    """
    app_home = path.dirname(path.realpath(__file__))

    data_ts = pd.read_csv(path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_timeseries_2_5_5_5_2.csv"), sep=";")

    model = Eesrep(solver=solver_for_tests, interface=interface_for_tests)

    source = FatalSource("source", (data_ts[["Time", "Input_0"]]).rename(columns={"Time":"time", "Input_0":"value"}))
    source_2 = FatalSource("source_2", (data_ts[["Time", "Input_1"]]).rename(columns={"Time":"time", "Input_1":"value"}))

    neural_network = NeuralNetwork("neural_network", 2, 2, 10000000.,
                                        path.join(app_home, "TestData", "DataSeries", "NeuralNetwork", "RN_coeffs_2_5_5_5_2.csv"))

    sink = Sink("sink", -10000000., 10000000., 1.)
    sink_2 = Sink("sink_2", -10000000., 10000000., 1.)
    
    model.add_component(source)
    model.add_component(source_2)
    model.add_component(neural_network)
    model.add_component(sink)    
    model.add_component(sink_2)

    model.add_link(source.power_out, neural_network.input_0, 1., 0.)
    model.add_link(source_2.power_out, neural_network.input_1, 1., 0.)
    model.add_link(neural_network.output_0, sink.power_in, 1., 0.)
    model.add_link(neural_network.output_1, sink_2.power_in, 1., 0.)

    model.define_time_range(3600., 100, 100, 3)

    model.solve(solve_parameters={SolverOption.PRINT_LOG:True})

    results = model.get_results(as_dataframe=True)

    theory = pd.read_csv(path.join(app_home, "TestData", "ReferenceResults", "NeuralNetwork", "RN_2_5_5_5_2_theory.csv"), sep = ",")
    assert max(abs(theory["Output_0"] - results["neural_network_output_0"])) < 1e-5
    assert max(abs(theory["Output_1"] - results["neural_network_output_1"])) < 1e-5
    assert max(abs(theory["Input_0"] - results["neural_network_input_0"])) < 1e-5

if __name__ == "__main__":
    test_nn_1_15_15_1()
