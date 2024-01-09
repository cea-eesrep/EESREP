"""EESREP sink/source model definitions.

These models are used to provide energy to the system, or pull energy from it. There are four components:

    - Source : energy input that is optimized, a price can be set.
    - FatalSource : energy input that is forced to the system.
    - Sink : energy output that is optimized, a price can be set.
    - FatalSink : energy output that is forced to the system.

"""
import pandas as pd

from eesrep.components.generic_component import GenericComponent
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_enum import TimeSerieType

class Source(GenericComponent):
    """The source component provides energy to the system. Its output is optimised in the MILP.
    
    Its parameters are the following:
    
        - p_min : output minimum value.
        - p_max : output maximum value.
        - price : price of the provided energy.

    The price variation time serie multiplies the price if provided.
    """

    def __init__(self, name:str, p_min:float, p_max:float, price:float, price_variation:pd.DataFrame = pd.DataFrame()):
        """Instanciates a source component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        p_min : float
            Minimal operating power
        p_max : float
            Maximal operating power
        price : float
            Price of each energy unit provided by the source
        price_variation : pd.DataFrame, optional
            Time serie that multiplies the price
        """

        self.name = name
        self.p_min = p_min
        self.p_max = p_max
        self.price = price

        self.time_series = {}

        if not price_variation.empty:
            if not "time" in price_variation.columns:
                raise KeyError("Column time absent from the price_variation parameter.")
            
            if not "value" in price_variation.columns:
                raise KeyError("Column value absent from the price_variation parameter.")

            self.time_series["price_variation"]={
                                                    "type": TimeSerieType.INTENSIVE,
                                                    "value": price_variation
                                                }

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
        variables["power_out"] = model_interface.get_new_continuous_variable_list(component_name+"_power_out_", len(time_steps), self.p_min, self.p_max)

        if "price_variation" in time_series:
            price_variation = time_series["price_variation"]
        else:
            price_variation = [1. for _ in range(len(time_steps))]

        objective = model_interface.sum_variables([self.price*variables["power_out"][i]*price_variation[i] for i in range(len(time_steps))])

        return variables, objective


class Sink(GenericComponent):
    """The sink component pulls energy from the system. Its input is optimised in the MILP.
    
    Its parameters are the following:
    
        - input : output minimum value.
        - input : output maximum value.
        - price : price of the provided energy.

    The price variation time serie multiplies the price if provided.
    """

    def __init__(self, name:str, p_min:float, p_max:float, price:float, price_variation:pd.DataFrame = pd.DataFrame()):
        """Instanciates a sink component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        p_min : float
            Minimal operating power
        p_max : float
            Maximal operating power
        price : float
            Price of each energy unit taken by the sink
        price_variation : pd.DataFrame, optional
            Time serie that multiplies the price
        """

        self.name = name
        self.p_min = p_min
        self.p_max = p_max
        self.price = price

        self.time_series = {}

        if not price_variation.empty:
            if not "time" in price_variation.columns:
                raise KeyError("Column time absent from the price_variation parameter.")
            
            if not "value" in price_variation.columns:
                raise KeyError("Column value absent from the price_variation parameter.")

            self.time_series["price_variation"]={
                                                    "type": TimeSerieType.INTENSIVE,
                                                    "value": price_variation
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

        variables["power_in"] = model_interface.get_new_continuous_variable_list(component_name+"_power_in_", len(time_steps), self.p_min, self.p_max)

        if "price_variation" in time_series:
            price_variation = time_series["price_variation"]
        else:
            price_variation = [1. for _ in range(len(time_steps))]

        objective = model_interface.sum_variables([self.price*variables["power_in"][i]*price_variation[i] for i in range(len(time_steps))])

        return variables, objective




class FatalSource(GenericComponent):
    """The fatal source component provides a fatal amount of energy to the system. 
    
    The amount provided is given by the source_flow time serie.
    """
    
    def __init__(self, name:str, source_flow:pd.DataFrame):
        """Instanciates a sink component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        source_flow : pd.DataFrame
            Time serie defining the flow of the falal source.
        """

        self.name = name

        self.time_series = {}

        if not source_flow.empty:

            if not "time" in source_flow.columns:
                raise KeyError("Column time absent from the source_flow parameter.")
            
            if not "value" in source_flow.columns:
                raise KeyError("Column value absent from the source_flow parameter.")

            self.time_series["source_flow"]={
                                                    "type": TimeSerieType.INTENSIVE,
                                                    "value": source_flow
                                                }

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

        variables["power_out"] = time_series["source_flow"]

        return variables, objective




class FatalSink(GenericComponent):
    """The fatal sink component pulls a fatal amount of energy from the system. 
    
    The amount pulled is given by the sink_flow time serie.
    """
    def __init__(self, name:str, sink_flow:pd.DataFrame):
        """Instanciates a fatal sink component with its options, to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the component.
        sink_flow : pd.DataFrame
            Time serie defining the flow of the fatal sink.
        """

        self.name = name

        self.time_series = {}

        if not sink_flow.empty:

            if not "time" in sink_flow.columns:
                raise KeyError("Column time absent from the sink_flow parameter.")
            
            if not "value" in sink_flow.columns:
                raise KeyError("Column value absent from the sink_flow parameter.")

            self.time_series["sink_flow"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": sink_flow
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

        variables["power_in"] = time_series["sink_flow"]

        return variables, objective
