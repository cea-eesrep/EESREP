"""EESREP storage component definition"""

import math

import pandas as pd

from eesrep.components.generic_component import GenericComponent
from eesrep.eesrep_enum import TimeSerieType
from eesrep.solver_interface.generic_interface import GenericInterface


class GenericStorage(GenericComponent):
    """Generic storage component definition.
    
    The generic storage is defined by the following parameters:
    
        - p_max : maximum input/output flux.
        - storage_max : maximum stored amount.
        - efficiency : loss while charging or discharging (counted twice if charge-discharge).
        - s_init : initial storage at the first solved horizon.
    
    The component has the following variables:

        - flow : charge/discharge flux (can be negative).
        - storage : amount stored at each time step.
    
    """
    def __init__(self, name:str, p_max:float, storage_max:float, efficiency:float, s_init:float):
        """Instanciates a storage component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        p_max : float
            Maximal operating power
        storage_max : float
            Storage capacity
        efficiency : float
            Efficiency of the storage
        s_init : float
            Price of each energy unit provided by the source
        """
        self.name = name
        self.p_max = p_max
        self.storage_max = storage_max
        self.efficiency = efficiency
        self.s_init = s_init

        self.time_series = {}

        self.flow = "flow"
        self.storage = "storage"

    def io_from_parameters(self) -> dict:
        """Lists the component Input/Outputs.

        Returns
        -------
        dict
            Dictionnary listing the Input/Outputs and their properties, each Input/Output has the two following keys:
                - type (TimeSerieType) : is the Input/Output intensive or extensive
                - continuity (bool) : is the Input/Output given in the next horizons history

        """
        return {
                    "flow":{
                                "type": TimeSerieType.INTENSIVE,
                                "continuity":False
                            },
                    "storage":{
                                "type": TimeSerieType.EXTENSIVE,
                                "continuity":True
                            }
                }

    def build_model(self,
        component_name:str,
        time_steps:list,
        time_series:pd.DataFrame,
        history:pd.DataFrame,
        model_interface:GenericInterface):
        """Builds the model at the current horizon.

        Parameters
        ----------
        component_name : str
            Component name to index the MILP variables
        time_steps : list
            List of the time steps length 
        time_series : pd.DataFrame
            Dataframe containing the time series values at the current horizon time steps.
        history : pd.DataFrame
            Dataframe with the variables of previous iterations if "continuity" is at true.
        model_interface : GenericInterface
            Solver interface used to provide the variables

        """
        
        objective = 0.
        variables = {}

        variables["flow"] = model_interface.get_new_continuous_variable_list(component_name+"_flow_", len(time_steps), -self.p_max, self.p_max)
        variables["storage"] = model_interface.get_new_continuous_variable_list(component_name+"_storage_", len(time_steps), 0., self.storage_max)

        if len(history) > 0:
            storage_init = history["storage"].iloc[-1]
        else:
            storage_init = self.s_init*self.storage_max

        model_interface.add_equality(model_interface.sum_variables([variables["storage"][0], -storage_init, -variables["flow"][0]*math.sqrt(self.efficiency)*time_steps[0]]), 0)
        
        for i in range(1, len(time_steps)):
            model_interface.add_equality(model_interface.sum_variables([variables["storage"][i], -variables["storage"][i-1], -variables["flow"][i]*math.sqrt(self.efficiency)*time_steps[i]]), 0)
        
        return variables, objective