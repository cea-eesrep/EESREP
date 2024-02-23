"""Class defining a component Input/Output"""

from .eesrep_enum import TimeSerieType

class ComponentIO:
    """
        Component Input/Output definition.
    """

    def __init__(self, component_name:str, io_name:str, io_type:TimeSerieType, io_continuity:bool):
        """_summary_

        Parameters
        ----------
        component_name : str
            Name of the component attached
        io_name : str
            Input/Output name
        io_type : TimeSerieType
            Wheter the IO is intensive or extensive
        io_continuity : bool
            Is the IO continuous between two horizons

        Raises
        ------
            TypeError
                Wrong type given for any parameter.
        """        
        if not isinstance(component_name, str):
            raise TypeError("component_name parameter should be a string.")
        if not isinstance(io_name, str):
            raise TypeError("io_name parameter should be a string.")
        if not isinstance(io_type, TimeSerieType):
            raise TypeError("io_type parameter should be a TimeSerieType.")
        if not isinstance(io_continuity, bool):
            raise TypeError("io_continuity parameter should be a boolean.")

        self.component_name:str = component_name
        self.io_name:str = io_name
        self.type:TimeSerieType = io_type
        self.continuity:bool = io_continuity

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.component_name == other.component_name and \
                self.io_name == other.io_name and \
                    self.type == other.type and \
                        self.continuity == other.continuity
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)