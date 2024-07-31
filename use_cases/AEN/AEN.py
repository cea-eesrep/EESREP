import pandas as pd

import eesrep
from eesrep.solver_options import SolverOption
from eesrep.components.bus import GenericBus
from eesrep.components.converter import Cluster, Converter
from eesrep.components.sink_source import FatalSink, FatalSource, Sink, Source
from eesrep.components.storage import GenericStorage

"""
    This use case consists in two lined area that both have:
        - A load time serie
        - PV production
        - Wind production
        - A storage 
        - the following thermal productions:
            Area 1:
            -	Nuclear 1 : 39*(Pmax : 1000 MW, Pmin : 500 MW) ;
            -	Nuclear 2 : 1*(Pmax : 700 MW, Pmin : 350 MW) ;
            -	CCGT  (Combined cycle gas turbine):: 46*(Pmax : 500 MW, Pmin : 150 MW) ;
            -	OCGT (Open cycle gas turbine): 1*(Pmax : 300 MW, Pmin : 75 MW).

            Area 2 : 
            -	Nuclear 1 : 41*(Pmax : 1000 MW, Pmin : 500 MW) ;
            -	Nuclear 2 : 1*(Pmax : 900 MW, Pmin : 450 MW) ;
            -	CCGT 1 : 26*(Pmax : 500 MW, Pmin : 150 MW) ;
            -	CCGT 2 : 1*(Pmax : 300 MW, Pmin : 90 MW) ;
            -	OCGT 1 : 40*(Pmax : 300 MW, Pmin : 75 MW) ;
            -	OCGT 2 : 1*(Pmax : 200 MW, Pmin : 50 MW).

            In both cases, the production means have the following properties: :
            -	Nuclear : 11,5 €/MWh, Minimal running time 8 h, Minimal shutdown time 24 h ;
            -	CCGT : 56,44 €/MWh, inimal running time 4 h, Minimal shutdown time 6 h ;
            -	OCGT : 96,11 €/MWh, inimal running time 1 h, Minimal shutdown time 1 h.
"""

data = pd.read_csv("AEN_timeseries.csv", sep=";")

model = eesrep.Eesrep(interface="docplex")

Zone_1 = GenericBus("Zone_1")

Load_1 = FatalSink(name="Load_1",
                                sink_flow=data[["Time", "Load_1"]].rename(columns={"Time":"time", "Load_1":"value"}))

Reseau_1 = Source(name="Reseau_1",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.)

Poubelle_1 = Sink(name="Poubelle_1",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.)

Storage_1 = GenericStorage(name="Storage_1",
                                    p_max=4500.,
                                    storage_max=4500.*7.*24./2.,
                                    efficiency=0.8,
                                    s_init=0.)

Solar_1  = FatalSource(name="Solar_1",
                                    source_flow=data[["Time", "Solar_1"]].rename(columns={"Time":"time", "Solar_1":"value"}))
Wind_1  = FatalSource(name="Wind_1",
                                    source_flow=data[["Time", "Wind_1"]].rename(columns={"Time":"time", "Wind_1":"value"}))
Hydro_ROR_1 = FatalSource(name="Hydro_ROR_1",
                                    source_flow=data[["Time", "Hydro_ROR_1"]].rename(columns={"Time":"time", "Hydro_ROR_1":"value"}))

OCGT_1 = Cluster(name="OCGT_1",
                                    efficiency=1.,
                                    p_max=300.,
                                    p_min=75.,
                                    n_machine_max=17,
                                    duration_on=1,
                                    duration_off=1,
                                    turn_on_price=15000.)

CCGT_1 = Cluster(name="CCGT_1",
                                    efficiency=1.,
                                    p_max=500.,
                                    p_min=150.,
                                    n_machine_max=46,
                                    duration_on=4,
                                    duration_off=6,
                                    turn_on_price=75000.)
                                
Nuclear_1 = Cluster(name="Nuclear_1",
                                    efficiency=1.,
                                    p_max=1000.,
                                    p_min=500.,
                                    n_machine_max=39,
                                    duration_on=8,
                                    duration_off=24,
                                    turn_on_price=500000.)

Nuclear_1_2 = Cluster(name="Nuclear_1_2",
                                    efficiency=1.,
                                    p_max=700.,
                                    p_min=350.,
                                    n_machine_max=1,
                                    duration_on=8,
                                    duration_off=24,
                                    turn_on_price=500000.)

Zone_2 = GenericBus("Zone_2")

Load_2 = FatalSink(name="Load_2",
                            sink_flow=data[["Time", "Load_2"]].rename(columns={"Time":"time", "Load_2":"value"}))

Reseau_2 = Source(name="Reseau_2",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.)

Poubelle_2 = Sink(name="Poubelle_2",
                                    p_min=0.,
                                    p_max=None,
                                    price=10000.)

Storage_2 = GenericStorage(name="Storage_2",
                                    p_max=8000.,
                                    storage_max=8000.*7.*24./2.,
                                    efficiency=0.8,
                                    s_init=0.)

Solar_2 = FatalSource(name="Solar_2", source_flow=data[["Time", "Solar_2"]].rename(columns={"Time":"time", "Solar_2":"value"}))
Wind_2 = FatalSource(name="Wind_2", source_flow=data[["Time", "Wind_2"]].rename(columns={"Time":"time", "Wind_2":"value"}))
Hydro_ROR_2 = FatalSource(name="Hydro_ROR_2", source_flow=data[["Time", "Hydro_ROR_2"]].rename(columns={"Time":"time", "Hydro_ROR_2":"value"}))

OCGT_2 = Cluster(name="OCGT_2",
                                efficiency=1.,
                                p_max=300.,
                                p_min=75.,
                                n_machine_max=40,
                                duration_on=1,
                                duration_off=1,
                                turn_on_price=15000.)

OCGT_2_2 = Cluster(name="OCGT_2_2",
                                efficiency=1.,
                                p_max=200.,
                                p_min=50.,
                                n_machine_max=1,
                                duration_on=1,
                                duration_off=1,
                                turn_on_price=15000.)

CCGT_2 = Cluster(name="CCGT_2",
                                efficiency=1.,
                                p_max=500.,
                                p_min=150.,
                                n_machine_max=26,
                                duration_on=4,
                                duration_off=6,
                                turn_on_price=75000.)

CCGT_2_2 = Cluster(name="CCGT_2_2",
                                efficiency=1.,
                                p_max=300.,
                                p_min=90.,
                                n_machine_max=1,
                                duration_on=4,
                                duration_off=6,
                                turn_on_price=75000.)
                                
Nuclear_2 = Cluster(name="Nuclear_2",
                                efficiency=1.,
                                p_max=1000.,
                                p_min=500.,
                                n_machine_max=41,
                                duration_on=8,
                                duration_off=24,
                                turn_on_price=500000.)

Nuclear_2_2 = Cluster(name="Nuclear_2_2",
                                efficiency=1.,
                                p_max=900.,
                                p_min=450.,
                                n_machine_max=1,
                                duration_on=8,
                                duration_off=24,
                                turn_on_price=500000.)

transfert_1_2 = Converter(name="transfert_1_2",
                                p_min=0.,
                                p_max=1000000.,
                                efficiency=1.)

transfert_2_1 = Converter(name="transfert_2_1",
                                p_min=0.,
                                p_max=1000000.,
                                efficiency=1.)

CCGT_bus = GenericBus("CCGT_bus")
Nuclear_bus = GenericBus("Nuclear_bus")
OCGT_bus = GenericBus("OCGT_bus")

Nuclear_fuel = Source(name="Nuclear_fuel",
                            p_min=0.,
                            p_max=None,
                            price=11.5)

CCGT_fuel = Source(name="CCGT_fuel",
                            p_min=0.,
                            p_max=None,
                            price=56.44)

OCGT_fuel = Source(name="OCGT_fuel",
                            p_min=0.,
                            p_max=None,
                            price=96.11)

for c in [Nuclear_fuel, 
            CCGT_fuel,
            OCGT_fuel,
    
            Load_1, 
            Poubelle_1, 
            Reseau_1,
            Solar_1,
            Wind_1,
            Hydro_ROR_1,
            OCGT_1,
            CCGT_1,
            Nuclear_1,
            Nuclear_1_2, 
            Storage_1,

            Load_2, 
            Poubelle_2, 
            Reseau_2,
            Solar_2,
            Wind_2,
            Hydro_ROR_2,
            OCGT_2,
            OCGT_2_2,
            CCGT_2,
            CCGT_2_2,
            Nuclear_2,
            Nuclear_2_2,
            Storage_2,

            transfert_1_2,
            transfert_2_1,
            
            Zone_1, 
            Zone_2, 
            CCGT_bus, 
            OCGT_bus, 
            Nuclear_bus]:
    model.add_component(c)

#   Plugging fuels inputs
model.plug_to_bus(Nuclear_fuel.power_out, Nuclear_bus.input, 1., 0.)
model.plug_to_bus(CCGT_fuel.power_out, CCGT_bus.input, 1., 0.)
model.plug_to_bus(OCGT_fuel.power_out, OCGT_bus.input, 1., 0.)

model.plug_to_bus(Nuclear_1.power_in, Nuclear_bus.output, 1., 0.)
model.plug_to_bus(Nuclear_1_2.power_in, Nuclear_bus.output, 1., 0.)
model.plug_to_bus(Nuclear_2.power_in, Nuclear_bus.output, 1., 0.)
model.plug_to_bus(Nuclear_2_2.power_in, Nuclear_bus.output, 1., 0.)

model.plug_to_bus(CCGT_1.power_in, CCGT_bus.output, 1., 0.)
model.plug_to_bus(CCGT_2.power_in, CCGT_bus.output, 1., 0.)
model.plug_to_bus(CCGT_2_2.power_in, CCGT_bus.output, 1., 0.)

model.plug_to_bus(OCGT_1.power_in, OCGT_bus.output, 1., 0.)
model.plug_to_bus(OCGT_2.power_in, OCGT_bus.output, 1., 0.)
model.plug_to_bus(OCGT_2_2.power_in, OCGT_bus.output, 1., 0.)


#   Zone 1
for component in [Load_1, Poubelle_1]:
    model.plug_to_bus(component.power_in, Zone_1.output, 1., 0.)

for component in [Reseau_1,
                Solar_1,
                Wind_1,
                Hydro_ROR_1,
                OCGT_1,
                CCGT_1,
                Nuclear_1,
                Nuclear_1_2]:
    model.plug_to_bus(component.power_out, Zone_1.input, 1., 0.)

model.plug_to_bus(Storage_1.flow, Zone_1.output, 1., 0.)

#   Zone 2
for component in [Load_2, Poubelle_2]:
    model.plug_to_bus(component.power_in, Zone_2.output, 1., 0.)

for component in [Reseau_2,
                Solar_2,
                Wind_2,
                Hydro_ROR_2,
                OCGT_2,
                OCGT_2_2,
                CCGT_2,
                CCGT_2_2,
                Nuclear_2,
                Nuclear_2_2]:
    model.plug_to_bus(component.power_out, Zone_2.input, 1., 0.)

model.plug_to_bus(Storage_2.flow, Zone_2.output, 1., 0.)

#   Transfers
model.plug_to_bus(transfert_1_2.power_in, Zone_1.output, 1., 0.)
model.plug_to_bus(transfert_1_2.power_out, Zone_2.input, 1., 0.)

model.plug_to_bus(transfert_2_1.power_in, Zone_2.output, 1., 0.)
model.plug_to_bus(transfert_2_1.power_out, Zone_1.input, 1., 0.)



model.define_time_range(3600., 168, 168, 52)

model.solve(solve_parameters={
                                SolverOption.MILP_GAP:0.001,
                                SolverOption.THREADS: 8,
                                "write_log":True,
                                SolverOption.WRITE_PROBLEM:True,
                                SolverOption.METHOD: "automatic",
                                "start_algorithm": "automatic"
                                # "time_limit": 10000.,
                                # "dual_prepro":True
                            })

model.get_results(as_dataframe=True).to_csv("AEN_results.csv")
