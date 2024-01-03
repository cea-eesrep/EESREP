"""
    This file defines the custom EESREP exceptions.
"""

#   Component creation related errors
class ComponentNameException(Exception):
    def __init__(self, component_name:str):
        super().__init__(f"No component named {component_name}.")

class ComponentTypeException(Exception):
    def __init__(self, component_type:str):
        super().__init__(f"No component registered at the name {component_type}.")

class BusTypeException(Exception):
    def __init__(self, component_type:str):
        super().__init__(f"No bus registered at the name {component_type}.")

class BusNameException(Exception):
    def __init__(self, component_type:str):
        super().__init__(f"No bus named {component_type}.")

class ParametersException(Exception):
    def __init__(self):
        super().__init__(f"Provided parameters or time series are not valid. Read the prints above.")

class TimeSerieException(Exception):
    def __init__(self, component_type:str, time_serie:str):
        super().__init__(f"Component {component_type} does not have a time serie called {time_serie}.")

class ComponentIOException(Exception):
    def __init__(self, component_type:str, io:str):
        super().__init__(f"Component named {component_type} has no input/output named {io}.")

class TimeSerieZeroException(Exception):
    def __init__(self, time_serie:str):
        super().__init__(f"The provided time serie '{time_serie}' time column doesn't start at 0.")





#   Solve related errors
class UnsolvableProblemException(Exception):
    def __init__(self):
        super().__init__("The given problem is not solvable.")

class UndefinedTimeRangeException(Exception):
    def __init__(self):
        super().__init__("Problem time range undefined.")
