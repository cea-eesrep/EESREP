"""

This file gives an example of post-processing function that draws and update a results plot at every solved rolling horizon.

This allows to see the results in real time.

"""


"""
    Imports
"""
import functools
import math
import pandas as pd

import eesrep
from eesrep.components.bus import GenericBus
from eesrep.components.sink_source import FatalSink, Source

import matplotlib.pyplot as plt

"""
    Model definition
"""
model = eesrep.Eesrep(interface="docplex")

zone = GenericBus("Zone_1")

load = FatalSink(name="load",
                                sink_flow=pd.DataFrame({"time":range(10000), "value":[abs(math.sin(i/200)) for i in range(10000)]}))

energy_source = Source(name="energy_source",
                                    p_min=0.,
                                    p_max=None,
                                    price=1.)

for c in [zone, 
            load,
            energy_source]:
    model.add_component(c)

model.plug_to_bus(load.power_in, zone.output, 1., 0.)
model.plug_to_bus(energy_source.power_out, zone.input, 1., 0.)

horizon_count = 30
model.define_time_range(1., 100, 100, horizon_count)

"""
    Plotter definition
"""
class Plotter:
    def __init__(self, horizon_count):     
        self.horizon_count = horizon_count
        self.iteration = 0 
        # to run GUI event loop
        plt.ion()
        
        # here we are creating sub plots
        self.figure, self.ax = plt.subplots(figsize=(10, 8))
        
        plt.show()

    def plot(self, df:pd.DataFrame):
        #   Clear the past graph
        self.ax.clear()
        
        #   Plot definition
        self.ax.plot(df["time"], df["energy_source_power_out"], label = "Energy source power out")

        plt.title(f"Plot at horizon {self.iteration}")
        
        plt.xlabel("Time (h)")
        plt.ylabel("Production (MW)")

        plt.legend()
    
        #   Display
        self.figure.canvas.flush_events()

        if self.iteration == self.horizon_count - 1:
            plt.show(block=True)

        self.iteration += 1
    
p = Plotter(horizon_count)

def update_plot(df:pd.DataFrame, p:Plotter):
    p.plot(df)

    return df

model.set_post_processing(functools.partial(update_plot, p=p))

"""
    Solve
"""
model.solve()