"""EESREP tool model components. It includes so far:

    - delayer: component whose output(t) = input(t-N)
"""
import pandas as pd

from eesrep.components.generic_component import GenericComponent
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_enum import TimeSerieType

class Delayer(GenericComponent):
    """Component whose output(t) = input(t-N).
    
    The time offset N is given by the parameter delay_time. 
    If t-N < 0 and we are solving the first horizon, the default_value is set as output.
    """
    def __init__(self, name:str, delay_time:int, default_value:float):
        """Instanciates a storage component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        delay_time : int
            Time step offset
        default_value : float
            Default value if before the simulation beginning
        """
        self.name = name
        self.delay_time = delay_time
        self.default_value = default_value

        self.time_series = {}

        self.power_in = "power_in"
        self.power_out = "power_out"

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
                    "power_in":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":True
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
        variables["power_out"] = model_interface.get_new_continuous_variable_list(component_name+"_power_out_", len(time_steps), None, None)

        for i in range(len(time_steps)):
            if i-self.delay_time >=0:
                model_interface.add_equality(model_interface.sum_variables([variables["power_out"][i],
                                                    -variables["power_in"][i-self.delay_time]]), 0)
            elif -(i-self.delay_time) <= len(history):
                model_interface.add_equality(model_interface.sum_variables([variables["power_out"][i],
                                                    -history["power_in"].iloc[i-self.delay_time]]), 0)
            else:
                model_interface.add_equality(model_interface.sum_variables([variables["power_out"][i],
                                                    -self.default_value]), 0)
        return variables, objective



class Integral(GenericComponent):
    """Component whose output(t) = sum(input(t-N), for N in range(integration_time)).
    
    If t-N < 0 and we are solving the first horizon, we count 0.
    """
    def __init__(self, name:str, integration_time:int):
        """Instanciates a storage component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        integration_time : int
            Time steps count of rolling integral
        """
        self.name = name
        self.integration_time = integration_time

        self.time_series = {}

        self.power_in = "power_in"
        self.power_out = "power_out"

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
                    "power_in":{
                                    "type": TimeSerieType.INTENSIVE,
                                    "continuity":True
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
        variables["power_out"] = model_interface.get_new_continuous_variable_list(component_name+"_power_out_", len(time_steps), None, None)

        for i in range(len(time_steps)):
            s = []

            for j in range(self.integration_time):
                if i-j >=0:
                    s.append(variables["power_in"][i-j])
                elif -(i-j) <= len(history):
                    s.append(history["power_in"].iloc[i-j])
            
            s.append(-variables["power_out"][i])
            model_interface.add_equality(model_interface.sum_variables(s), 0)

        return variables, objective

class LowerThan(GenericComponent):
    """Component that adds a lower than constraint on its input to a value or a given time serie.
    """
    def __init__(self, name:str, value:float, value_serie:pd.DataFrame = pd.DataFrame()):
        """Instanciates a lower_than component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        value : float
            Value to be lower than.
        value_serie : pd.DataFrame, optional
            Time serie than can replace the value parameter

        """
        self.name = name
        self.value = value

        self.time_series = {}
        
        if not value_serie.empty:
            if not "time" in value_serie.columns:
                raise KeyError("Column time absent from the value_serie parameter.")
            
            if not "value" in value_serie.columns:
                raise KeyError("Column value absent from the value_serie parameter.")

            self.time_series["value_serie"]={
                                                    "type": TimeSerieType.INTENSIVE,
                                                    "value": value_serie
                                                }

        self.power_in = "power_in"

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
                    "power_in":{
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

        for i in range(len(time_steps)):
            if "value_serie" in time_series:
                model_interface.add_lower_than(variables["power_in"][i], time_series.loc[i, "value_serie"])
            else:
                model_interface.add_lower_than(variables["power_in"][i], self.value)

        return variables, objective

class GreaterThan(GenericComponent):
    """Component that adds a greater than constraint on its input to a value or a given time serie.
    """
    def __init__(self, name:str, value:float, value_serie:pd.DataFrame = pd.DataFrame()):
        """Instanciates a greater_than component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        value : float
            Value to be greater than.
        value_serie : pd.DataFrame, optional
            Time serie than can replace the value parameter

        """
        self.name = name
        self.value = value

        self.time_series = {}
        
        if not value_serie.empty:
            if not "time" in value_serie.columns:
                raise KeyError("Column time absent from the value_serie parameter.")
            
            if not "value" in value_serie.columns:
                raise KeyError("Column value absent from the value_serie parameter.")

            self.time_series["value_serie"]={
                                                    "type": TimeSerieType.INTENSIVE,
                                                    "value": value_serie
                                                }

        self.power_in = "power_in"

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
                    "power_in":{
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

        for i in range(len(time_steps)):
            if "value_serie" in time_series:
                model_interface.add_greater_than(variables["power_in"][i], time_series.loc[i, "value_serie"])
            else:
                model_interface.add_greater_than(variables["power_in"][i], self.value)

        return variables, objective
