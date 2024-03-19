"""Class defining a bus"""

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

    def get_submodel_version(self, submodel_name:str):
        self.submodel_name = submodel_name

        return self
