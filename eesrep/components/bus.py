"""EESREP bus components.
"""

from typing import Dict, List, Tuple

from eesrep.components.generic_component import GenericComponent
from eesrep.eesrep_enum import TimeSerieType
from eesrep.eesrep_io import ComponentIO


class GenericBus(GenericComponent):
    """Generic bus class.

    Build_model function is not defined as it is bypassed by EESREP core. 
    """
    def __init__(self, name:str):
        """Generic bus class with input and output IO.

        Parameters
        ----------
        name : str
            Name of the component.
        """
        self.name:str = name

        self.time_series = {}

        self.input:ComponentIO = ComponentIO(self.name, "input", TimeSerieType.INTENSIVE, False)
        self.output:ComponentIO = ComponentIO(self.name, "output", TimeSerieType.INTENSIVE, False)

        self.inputs:List[Tuple[ComponentIO, float, float]] = []
        self.outputs:List[Tuple[ComponentIO, float, float]] = []

    def io_from_parameters(self) -> Dict[str, ComponentIO]:
        """Lists the component Input/Outputs.

        Returns
        -------
        dict
            Dictionnary listing the Input/Outputs and their respective ComponentIO objects

        """
        return {
                    "input": self.input,
                    "output": self.output
                }
