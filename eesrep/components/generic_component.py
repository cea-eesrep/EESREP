"""This class contains the EESREP generic component class.

All component registered to EESREP must inherit from GenericComponent and override the functions
defined here:

    -   model_definition : gives a dictionnary of parameters, that provides the user the required parameters to define the model component.
    -   io_from_parameters : returns the Input/Outputs of a component, provided a set of parameters.
    -   build_model : creates the model component variables and constraints.
"""
from typing import Dict, List

import pandas as pd
from eesrep.eesrep_io import ComponentIO

from eesrep.solver_interface.generic_interface import GenericInterface


class GenericComponent:
    """EESREP generic model class"""

    def __init__(self):
        self.name:str = ""
        self.time_series = {}
        raise NotImplementedError

    def model_definition(self) -> dict:
        """Returns the model definitions

        Returns
        -------
        dict
            Dictionnary defining the parameters, time series and the function definition of the component.

        Raises
        ------
        NotImplementedError
            Needs to be overloaded by the inheriting components.
        """
        raise NotImplementedError

    def io_from_parameters(self) -> Dict[str, ComponentIO]:
        """Lists the component Input/Outputs.

        Returns
        -------
        dict
            Dictionnary listing the Input/Outputs and their respective ComponentIO objects

        Raises
        ------
        NotImplementedError
            Needs to be overloaded by the inheriting components.
        """
        raise NotImplementedError

    def build_model(self,
        component_name:str,
        time_steps:List[float],
        time_series:pd.DataFrame,
        history:pd.DataFrame,
        model_interface:GenericInterface,
        future:pd.DataFrame = None):
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
            Dataframe with the history of variables of previous iterations if "continuity" is at true.
        model_interface : GenericInterface
            Solver interface used to provide the variables
        future : pd.DataFrame
            Dataframe with the previsions of variables of previous iterations if "continuity" is at true.

        Raises
        ------
        NotImplementedError
            Needs to be overloaded by the inheriting components.
        """
        raise NotImplementedError

    def get_time_series(self) -> dict:
        try:
            return self.time_series
        except AttributeError:
            raise AttributeError("time_series is not an attribute of the custom component.")