"""This file contains the EESREP components that can be used as converter. In EESREP, converters
typically have a power_in, power_out, and a set of constraints that condition its behavior.

Two types are initially implemented:

    -   Converter : the output corresponds to the input multiplied by an efficiency.
    -   Cluster : models the behavior of N machines, that can be turned on and off."""

import pandas as pd

from eesrep.components.generic_component import GenericComponent
from eesrep.eesrep_enum import TimeSerieType
from eesrep.solver_interface.generic_interface import GenericInterface


class Converter(GenericComponent):
    """EESREP converter model :
        The converter output equals input * efficiency
    """

    def __init__(self, name:str, efficiency:float, p_min:float, p_max:float):
        """Instanciates a converter with its options, to provide to EESREP

        Parameters
        ----------
        name : str
            Name of the component.
        efficiency : float
            Efficiency of the converter (models the component losses)
        p_min : float
            Minimal operating power
        p_max : float
            Maximal operating power
        """

        self.name = name
        self.efficiency = efficiency
        self.p_min = p_min
        self.p_max = p_max

        self.time_series = {}

        self.power_in = "power_in"
        self.power_out = "power_out"

    def io_from_parameters(self) -> dict:
        """Lists the component Input/Output based on the component parameters.

        Returns
        -------
        dict
            Dictionnary listing the Input/Outputs and their properties, each Input/Output has the two following keys:
                - type (TimeSerieType) : is the Input/Output intensive or extensive
                - continuity (bool) : is the Input/Output given in the next horizons history

        """
        return {
                    "power_in":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":False
                                },
                    "power_out":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":False
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

        variables["power_in"] = model_interface.get_new_continuous_variable_list(component_name+"_power_in_", len(time_steps), None, None)
        variables["power_out"] = model_interface.get_new_continuous_variable_list(component_name+"_power_out_", len(time_steps), self.p_min, self.p_max)

        for i in range(len(time_steps)):
            model_interface.add_equality(model_interface.sum_variables([variables["power_out"][i], -variables["power_in"][i]*self.efficiency]), 0)

        return variables, objective





class Cluster(GenericComponent):
    """The cluster models N machine that can be turned on and off. Its parameters are the following:

            -   power_out = power_in * efficiency.
            -   power_out is lower than N running machines * p_max.
            -   power_out is greater than N running machines * p_min.
            -   the running machine count is lower than n_machine_max.
            -   a machine must work for duration_on timesteps after being turned on.   
            -   a machine must remain off for duration_on timesteps after being turned off.
            -   turn_on_price is added to the objective at each machine turn-on.
    """

    def __init__(self, name:str,
                        efficiency:float,
                        p_min:float,
                        p_max:float,
                        n_machine_max:int,
                        duration_on:int,
                        duration_off:int,
                        turn_on_price:float):
        """_summary_

        Parameters
        ----------
        name : str
            Name of the component.
        efficiency : float
            Efficiency of the converter (models the component losses)
        p_min : float
            Minimal operating power
        p_max : float
            Maximal operating power
        n_machine_max : int
            Maximum number of machines
        duration_on : int
            Minimum working time of a turned-on machine
        duration_off : int
            Minimum shut down time of a turned-off machine
        turn_on_price : float
            Price of turning-on a machine
        """        

        self.name = name
        self.efficiency = efficiency
        self.p_min = p_min
        self.p_max = p_max
        self.n_machine_max = n_machine_max
        self.duration_on = duration_on
        self.duration_off = duration_off
        self.turn_on_price = turn_on_price

        self.time_series = {}

        self.power_in = "power_in"
        self.power_out = "power_out"
        self.n_machine = "n_machine"
        self.turn_on = "turn_on"
        self.turn_off = "turn_off"
        self.turn_on_count = "turn_on_count"
        self.turn_off_count = "turn_off_count"

    def io_from_parameters(self) -> dict:
        """Lists the component Input/Outputs based on the component parameters.

        Returns
        -------
        dict
            Dictionnary listing the Input/Outputs and their properties, each Input/Output has the two following keys:
                - type (TimeSerieType) : is the Input/Output intensive or extensive
                - continuity (bool) : is the Input/Output given in the next horizons history

        """
        return {
                    "power_in":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":False
                                },
                    "power_out":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":False
                                },
                    "n_machine":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":True
                                },
                    "turn_on":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":True
                                },
                    "turn_off":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":True
                                },
                    "turn_on_count":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":True
                                },
                    "turn_off_count":{
                                    "type": TimeSerieType.INTENSIVE,
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
        parameters : dict
            Component parameters dictionnary
        time_series : pd.DataFrame
            Dataframe containing the time series values at the current horizon time steps.
        history : pd.DataFrame
            Dataframe with the variables of previous iterations if "continuity" is at true.
        model_interface : GenericInterface
            Solver interface used to provide the variables

        """

        objective = 0.
        variables = {}

        variables["power_in"] = model_interface.get_new_continuous_variable_list(component_name+"_power_in_", len(time_steps), None, None)
        variables["power_out"] = model_interface.get_new_continuous_variable_list(component_name+"_power_out_", len(time_steps), None, None)

        variables["turn_on"] = model_interface.get_new_continuous_variable_list(component_name+"_turn_on_", len(time_steps), 0., None)
        variables["turn_off"] = model_interface.get_new_continuous_variable_list(component_name+"_turn_off_", len(time_steps), 0., None)
        variables["turn_on_count"] = model_interface.get_new_continuous_variable_list(component_name+"_turn_on_count_", len(time_steps), None, None)
        variables["turn_off_count"] = model_interface.get_new_continuous_variable_list(component_name+"_turn_off_count_", len(time_steps), None, None)

        variables["n_machine"] = model_interface.get_new_discrete_variable_list(component_name+"_n_machine_in_", len(time_steps), 0., self.n_machine_max)

        for i in range(len(time_steps)):
            #   Power_out = f(Power_in)
            model_interface.add_equality(model_interface.sum_variables([variables["power_out"][i], -variables["power_in"][i]*self.efficiency]), 0)
            
            #   Constraints Power_out
            model_interface.add_lower_than(model_interface.sum_variables([variables["power_out"][i], -variables["n_machine"][i]*self.p_max]), 0)
            model_interface.add_greater_than(model_interface.sum_variables([variables["power_out"][i], -variables["n_machine"][i]*self.p_min]), 0)

            #   Counts Turn_on and Turn_off
            arr_turn_on = []
            for j in range(self.duration_on-1):
                if i-j >= 0:
                    arr_turn_on.append(variables["turn_on"][i-j])
                elif len(history) > 0 and len(history)+i-j >= 0:
                    arr_turn_on.append(history["turn_on"].iloc[len(history)+i-j])

            variables["turn_on_count"][i] = model_interface.sum_variables(arr_turn_on)

            arr_turn_off = []
            for j in range(self.duration_off-1):
                if i-j >= 0:
                    arr_turn_off.append(variables["turn_off"][i-j])
                elif len(history) > 0 and len(history)+i-j >= 0:
                    arr_turn_off.append(history["turn_off"].iloc[len(history)+i-j])

            variables["turn_off_count"][i] = model_interface.sum_variables(arr_turn_off)

            #   Constraints machine number
            if i == 0 and len(history) == 0:
                #   Counts n_machine changes
                model_interface.add_equality(model_interface.sum_variables([variables["n_machine"][i], variables["turn_off"][i], -variables["turn_on"][i]]), 0)

            elif i == 0 and len(history) > 0:
                #   Counts n_machine changes
                model_interface.add_equality(model_interface.sum_variables([variables["n_machine"][i], -history["n_machine"].iloc[-1], variables["turn_off"][i], -variables["turn_on"][i]]), 0)

                #   Limits turn off
                model_interface.add_lower_than(model_interface.sum_variables([variables["turn_off"][i], -history["n_machine"].iloc[-1], history["turn_on_count"].iloc[-1]]), 0)

                #   Limits turn on
                model_interface.add_lower_than(model_interface.sum_variables([variables["turn_on"][i], -self.n_machine_max, history["n_machine"].iloc[-1], history["turn_off_count"].iloc[-1]]), 0)

            else:
                #   Counts n_machine changes
                model_interface.add_equality(model_interface.sum_variables([variables["n_machine"][i], -variables["n_machine"][i-1], variables["turn_off"][i], -variables["turn_on"][i]]), 0)
                
                #   Limits turn off
                model_interface.add_lower_than(model_interface.sum_variables([variables["turn_off"][i], -variables["n_machine"][i-1], variables["turn_on_count"][i-1]]), 0)
            
                #   Limits turn on
                model_interface.add_lower_than(model_interface.sum_variables([variables["turn_on"][i], -self.n_machine_max, variables["n_machine"][i-1], variables["turn_off_count"][i-1]]), 0)

        objective = model_interface.sum_variables([variables["turn_on"][i] * self.turn_on_price for i in range(len(time_steps))])

        return variables, objective
