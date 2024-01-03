import pandas as pd

import eesrep
from eesrep.components.sink_source import FatalSink, Source, FatalSource, Sink
from eesrep.components.converter import Converter, Cluster
from eesrep.components.storage import GenericStorage

data = pd.read_csv("AEN_timeseries.csv", sep=";")

model = eesrep.Eesrep(solver="DOCPLEX")

model.create_bus("bus", {
                            "name":"Zone_1"
                        })

model.add_component(FatalSink(name="Load_1",
                                sink_flow=data[["Time", "Load_1"]].rename(columns={"Time":"time", "Load_1":"value"})))

model.add_component(Source(name="Reseau_1",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.))

model.add_component(Sink(name="Poubelle_1",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.))

model.add_component(GenericStorage(name="Storage_1",
                                    p_max=4500.,
                                    storage_max=4500.*7.*24./2.,
                                    efficiency=0.8,
                                    s_init=0.))

for enr in ["Solar_1", "Wind_1", "Hydro_ROR_1"]:
    model.add_component(FatalSource(name=enr,
                                    source_flow=data[["Time", enr]].rename(columns={"Time":"time", enr:"value"})))

model.add_component(Cluster(name="OCGT_1",
                                    efficiency=1.,
                                    p_max=300.,
                                    p_min=75.,
                                    n_machine_max=17,
                                    duration_on=1,
                                    duration_off=1,
                                    turn_on_price=15000.))

model.add_component(Cluster(name="CCGT_1",
                                    efficiency=1.,
                                    p_max=500.,
                                    p_min=150.,
                                    n_machine_max=46,
                                    duration_on=4,
                                    duration_off=6,
                                    turn_on_price=75000.))
                                
model.add_component(Cluster(name="Nuclear_1",
                                    efficiency=1.,
                                    p_max=1000.,
                                    p_min=500.,
                                    n_machine_max=39,
                                    duration_on=8,
                                    duration_off=24,
                                    turn_on_price=500000.))

model.add_component(Cluster(name="Nuclear_1_2",
                                    efficiency=1.,
                                    p_max=700.,
                                    p_min=350.,
                                    n_machine_max=1,
                                    duration_on=8,
                                    duration_off=24,
                                    turn_on_price=500000.))

model.create_bus("bus", {
                            "name":"Zone_2"
                        })

model.add_component(FatalSink(name="Load_2",
                            sink_flow=data[["Time", "Load_2"]].rename(columns={"Time":"time", "Load_2":"value"})))

model.add_component(Source(name="Reseau_2",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.))

model.add_component(Sink(name="Poubelle_2",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.))

model.add_component(GenericStorage(name="Storage_2",
                                    p_max=8000.,
                                    storage_max=8000.*7.*24./2.,
                                    efficiency=0.8,
                                    s_init=0.))

for enr in ["Solar_2", "Wind_2", "Hydro_ROR_2"]:
    model.add_component(FatalSource(name=enr,
                                    source_flow=data[["Time", enr]].rename(columns={"Time":"time", enr:"value"})))

model.add_component(Cluster(name="OCGT_2",
                                efficiency=1.,
                                p_max=300.,
                                p_min=75.,
                                n_machine_max=40,
                                duration_on=1,
                                duration_off=1,
                                turn_on_price=15000.))

model.add_component(Cluster(name="OCGT_2_2",
                                efficiency=1.,
                                p_max=200.,
                                p_min=50.,
                                n_machine_max=1,
                                duration_on=1,
                                duration_off=1,
                                turn_on_price=15000.))

model.add_component(Cluster(name="CCGT_2",
                                efficiency=1.,
                                p_max=500.,
                                p_min=150.,
                                n_machine_max=26,
                                duration_on=4,
                                duration_off=6,
                                turn_on_price=75000.))

model.add_component(Cluster(name="CCGT_2_2",
                                efficiency=1.,
                                p_max=300.,
                                p_min=90.,
                                n_machine_max=1,
                                duration_on=4,
                                duration_off=6,
                                turn_on_price=75000.))
                                
model.add_component(Cluster(name="Nuclear_2",
                                efficiency=1.,
                                p_max=1000.,
                                p_min=500.,
                                n_machine_max=41,
                                duration_on=8,
                                duration_off=24,
                                turn_on_price=500000.))

model.add_component(Cluster(name="Nuclear_2_2",
                                efficiency=1.,
                                p_max=900.,
                                p_min=450.,
                                n_machine_max=1,
                                duration_on=8,
                                duration_off=24,
                                turn_on_price=500000.))

model.add_component(Converter(name="transfert_1_2",
                                p_min=0.,
                                p_max=1000000.,
                                efficiency=1.))

model.add_component(Converter(name="transfert_2_1",
                                p_min=0.,
                                p_max=1000000.,
                                efficiency=1.))

model.create_bus("bus", {
                            "name":"CCGT_bus"
                        })
model.create_bus("bus", {
                            "name":"Nuclear_bus"
                        })
model.create_bus("bus", {
                            "name":"OCGT_bus"
                        })

model.add_component(Source(name="Nuclear_fuel",
                            p_min=0.,
                            p_max=None,
                            price=11.5))

model.add_component(Source(name="CCGT_fuel",
                            p_min=0.,
                            p_max=None,
                            price=56.44))

model.add_component(Source(name="OCGT_fuel",
                            p_min=0.,
                            p_max=None,
                            price=96.11))

#   Plugging fuels inputs
model.plug_to_bus("Nuclear_fuel", "power_out", "Nuclear_bus", True, 1., 0.)
model.plug_to_bus("CCGT_fuel", "power_out", "CCGT_bus", True, 1., 0.)
model.plug_to_bus("OCGT_fuel", "power_out", "OCGT_bus", True, 1., 0.)

model.plug_to_bus("Nuclear_1", "power_in", "Nuclear_bus", False, 1., 0.)
model.plug_to_bus("Nuclear_1_2", "power_in", "Nuclear_bus", False, 1., 0.)
model.plug_to_bus("Nuclear_2", "power_in", "Nuclear_bus", False, 1., 0.)
model.plug_to_bus("Nuclear_2_2", "power_in", "Nuclear_bus", False, 1., 0.)

model.plug_to_bus("CCGT_1", "power_in", "CCGT_bus", False, 1., 0.)
model.plug_to_bus("CCGT_2", "power_in", "CCGT_bus", False, 1., 0.)
model.plug_to_bus("CCGT_2_2", "power_in", "CCGT_bus", False, 1., 0.)

model.plug_to_bus("OCGT_1", "power_in", "OCGT_bus", False, 1., 0.)
model.plug_to_bus("OCGT_2", "power_in", "OCGT_bus", False, 1., 0.)
model.plug_to_bus("OCGT_2_2", "power_in", "OCGT_bus", False, 1., 0.)


#   Zone 1
for component in [["Load_1", "power_in"],
                ["Poubelle_1", "power_in"]]:
    model.plug_to_bus(component[0], component[1], "Zone_1", False, 1., 0.)

for component in [["Reseau_1", "power_out"],
                ["Solar_1", "power_out"],
                ["Wind_1", "power_out"],
                ["Hydro_ROR_1", "power_out"],
                ["OCGT_1", "power_out"],
                ["CCGT_1", "power_out"],
                ["Nuclear_1", "power_out"],
                ["Nuclear_1_2", "power_out"]]:
    model.plug_to_bus(component[0], component[1], "Zone_1", True, 1., 0.)

model.plug_to_bus("Storage_1", "flow", "Zone_1", False, 1., 0.)

#   Zone 2
for component in [["Load_2", "power_in"],
                ["Poubelle_2", "power_in"]]:
    model.plug_to_bus(component[0], component[1], "Zone_2", False, 1., 0.)

for component in [["Reseau_2", "power_out"],
                ["Solar_2", "power_out"],
                ["Wind_2", "power_out"],
                ["Hydro_ROR_2", "power_out"],
                ["OCGT_2", "power_out"],
                ["OCGT_2_2", "power_out"],
                ["CCGT_2", "power_out"],
                ["CCGT_2_2", "power_out"],
                ["Nuclear_2", "power_out"],
                ["Nuclear_2_2", "power_out"]]:
    model.plug_to_bus(component[0], component[1], "Zone_2", True, 1., 0.)

model.plug_to_bus("Storage_2", "flow", "Zone_2", False, 1., 0.)

#   Transfers
model.plug_to_bus("transfert_1_2", "power_in", "Zone_1", False, 1., 0.)
model.plug_to_bus("transfert_1_2", "power_out", "Zone_2", True, 1., 0.)

model.plug_to_bus("transfert_2_1", "power_in", "Zone_2", False, 1., 0.)
model.plug_to_bus("transfert_2_1", "power_out", "Zone_1", True, 1., 0.)



model.define_time_range(3600., 168, 168, 52)

model.solve(solve_parameters={
                                "gap":0.001,
                                "threads": 8,
                                "write_log":True,
                                "write_problem":True,
                                "method": "automatic",
                                "start_algorithm": "automatic"
                                # "time_limit": 10000.,
                                # "dual_prepro":True
                            })

model.get_results(as_dataframe=True).to_csv("AEN_results.csv")
