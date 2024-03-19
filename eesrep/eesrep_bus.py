"""Class defining a bus"""

from typing import List, Tuple

import pandas as pd
from eesrep.solver_interface.generic_interface import GenericInterface


class ComponentBUS:
    """
        Bus component.
    """

    def __init__(self, bus_name:str):
        """_summary_

        Parameters
        ----------
        bus_name : str
            Name of the bus
        """      
        self.name:str = bus_name
        self.submodel_name:str = None
        self.inputs:List[Tuple[str, str, float, float]] = []
        self.outputs:List[Tuple[str, str, float, float]] = []

    def get_submodel_version(self, submodel_name:str):
        if submodel_name == "":
            return self
        else:
            self.submodel_name = submodel_name

            return self
