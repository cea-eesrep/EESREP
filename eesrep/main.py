"""EESREP model builder and solver module"""

from typing import Any, Callable, Dict, List

import numpy as np
import pandas as pd

from .components.generic_component import GenericComponent
from .eesrep_exceptions import *
from .solver_interface.generic_interface import GenericInterface
from .solver_interface.interface_tester import InterfaceTester

try:
    from .solver_interface.docplex_interface import DocplexInterface
except ImportError:
    class DocplexInterface:
        """ Fake DocplexInterface class for import error management. """
        def __init__(self, direction:str = "Minimize", solver:str = "CPLEX"):
            raise ImportError("Error while importing Docplex Interface. Make sure you have the docplex module installed.")

try:
    from .solver_interface.cplex_interface import CplexInterface
except ImportError:
    class CplexInterface:
        """ Fake DocplexInterface class for import error management. """
        def __init__(self, direction:str = "Minimize", solver:str = "CPLEX"):
            raise ImportError("Error while importing Cplex Interface. Make sure you have the cplex module installed.")

try:
    from .solver_interface.mip_interface import MIPInterface
except ImportError:
    class MIPInterface:
        """ Fake MIPInterface class for import error management. """
        def __init__(self, direction:str = "Minimize", solver:str = "CPLEX"):
            raise ImportError("Error while importing MIP Interface. Make sure you have the mip module installed.")

try:
    from .solver_interface.pyomo_interface import PyomoInterface
except ImportError:
    class PyomoInterface:
        """ Fake PyomoInterface class for import error management. """
        def __init__(self, direction:str = "Minimize", solver:str = "CPLEX"):
                raise ImportError("Error while importing Pyomo Interface. Make sure you have the pyomo module installed.")

from .eesrep_enum import TimeSerieType


class Eesrep:
    """
        ESREP model builder and solver class
    
    """

    #@profile
    def __init__(self, direction:str = "Minimize", interface:str = "mip", solver:str = "CBC"):
        """EESREP class constructor

        Parameters
        ----------
        direction : str, optional
            Tells if the objective is to Minimize or Maximize. Defaults to "Minimize".
        interface : str, optional
            Solver/Python module name to use, choose among ["mip", "docplex", "pyomo"] or any custom registered interface. Defaults to "mip".
        solver : str, optional
            Solver/Python module name to use, is interface at mip, we suggest using CBC or Gurobi, if docplex, solver is set at CPLEX, if Pyomo, see the module compatible solvers. Defaults to "CBC".
        """
        self.__solver: str = solver
        self.__interface: str = interface
        self.__direction: str = direction

        self.__custom_interfaces: Dict[str, GenericInterface] = {}

        self.__model : GenericInterface = None

        self.__components: Dict[str, GenericComponent] = {}
        self.__variables: Dict[str, Dict] = {}
        self.__buses: Dict[str, Dict[str, List[str or float]]] = {}
        self.__results: pd.DataFrame = pd.DataFrame()
        self.__links: List[str, Any, str, Any , float, float] = []

        self.__time_series: pd.DataFrame = pd.DataFrame()

        self.__current_time: float = 0.
        self.__steps_solved: int = 0

        self.__objective: int = 0.

        self.__time_range_defined: bool = False

        self.__component_definition: Dict[str, Callable] = {}

        self.time_step: float = -1
        self.time_shift: int = -1
        self.future_size: int = -1
        self.horizon_count: int = -1
        self.custom_steps: List[float] = []
        self.solve_parameters: dict = {}

        self._register_default_components()

    #@profile
    def create_model_interface(self):
        """
            Creates the model interface object from the solver name.

            Raises
            ------
                ValueError: The solver argument provided while creating an Eesrep object is not correct.
        """
        if self.__interface.lower() not in ["mip", "docplex", "cplex", "pyomo"] + list(self.__custom_interfaces.keys()):
            raise ValueError(
                f"Interface name {self.__interface} is not implemented, please use: mip, pyomo, docplex or register your interface first.")

        if self.__interface in self.__custom_interfaces:
            self.__model = self.__custom_interfaces[self.__interface](direction = self.__direction , solver = self.__solver)

        elif self.__interface.lower() == "mip":
            self.__model = MIPInterface(direction = self.__direction , solver = self.__solver)

        elif self.__interface.lower() == "docplex":
            self.__solver = "CPLEX"
            self.__model = DocplexInterface(direction = self.__direction)

        elif self.__interface.lower() == "cplex":
            self.__solver = "CPLEX"
            self.__model = CplexInterface(direction = self.__direction)

        elif self.__interface.lower() == "pyomo":
            self.__model = PyomoInterface(direction = self.__direction, solver=self.__solver)

    #@profile
    def register_solver_interface(self, interface_name:str, interface:GenericInterface):
        """Registers a user made solver interface. Custom solver interfaces will be tested before
        built-in solver interfaces. It is therefore possible to overwrite a built-in interface.

        Parameters
        ----------
        interface_name : str
            Name under which the interface will be registered.
        interface : GenericInterface
            Custom solver interface

        Raises
        ------
        ValueError
            Custom solver interface already exists with this key.
        """
        if interface_name in self.__custom_interfaces or interface_name.lower() in ["cbc", "gurobi", "cplex", "pyomo"]:
            raise ValueError(f"A custom interface already exists at the key '{interface_name}'")

        tester = InterfaceTester()

        tester.test(interface)

        self.__custom_interfaces[interface_name] = interface

        self.__interface = interface_name

    #@profile
    def _register_default_components(self):
        """Function that registers the built-in components.

        The bus component is defined here as it has a different behavior than other components.
        """
        self.__component_definition["bus"]={
                                                "parameters":{
                                                                "name":str,
                                                             },
                                                "variables":{},
                                                "time_series":
                                                            {},
                                                "definition":self._create_bus
                                            }

    #@profile
    def add_component(self, component:GenericComponent):
        """Adds a component to the model.

        Parameters
        ----------
        component : GenericComponent
            Component of a class that inherits from GenericComponent.

        Raises
        ------
        ValueError
            A component is already registered with this name.
        TypeError
            Provided component is not a Generic Component.
        AttributeError
            'name' absent from the object attributes.
        TypeError
            One of the time series definition is not a dictionnary.
        KeyError
            One of the time series definition dictionnary has wrong keys.
        TypeError
            One of the time series type is not a TimeSerieType.
        TypeError
            One of the time series 'value' parameter is not a pandas DataFrame.
        TypeError
            The 'value' dataframe does not have the right columns.
        """
        if not isinstance(component, GenericComponent):
            raise TypeError("Provided component is not a Generic Component")

        try:
            name = component.name
        except AttributeError:
            raise AttributeError("Provided component does not have a 'name' attribute.")

        if name in self.__components:
            raise ValueError(f"Component {name} already exists.")

        time_series = component.get_time_series()

        if not isinstance(time_series, dict):
            raise TypeError(f"The time series definition is not a dictionnary.")

        for ts in time_series.values():
            if not isinstance(ts, dict):
                raise TypeError(f"'{ts}' time serie definition is not a dictionnary.")

            if not sorted(list(ts.keys())) == ["type", "value"]:
                raise KeyError(f"'{ts}' time serie definition dictionnary does not have the right keys, should be ['type', 'value'].")
            
            if not isinstance(ts["type"], TimeSerieType):
                raise TypeError(f"'{ts}' time serie 'type' is not a member of TimeSerieType enum.")
            
            if not isinstance(ts["value"], pd.DataFrame):
                raise TypeError(f"'{ts}' time serie 'value' is not pandas DataFrame.")

            if not sorted(list(ts["value"].columns)) == ["time", "value"]:
                raise KeyError(f"'{ts}' time serie value definition does not have the right columns, should be ['time', 'value'].")

        io = component.io_from_parameters()
        
        if not isinstance(io, dict):
            raise TypeError(f"The input/output definition is not a dictionnary.")

        for elem in io.values():
            if not isinstance(elem, dict):
                raise TypeError(f"'{elem}' io definition is not a dictionnary.")

            if not sorted(list(elem.keys())) == ["continuity", "type"]:
                raise KeyError(f"'{elem}' io definition dictionnary does not have the right keys, should be ['type', 'continuity'].")
            
            if not isinstance(elem["type"], TimeSerieType):
                raise TypeError(f"'{elem}' io 'type' is not a member of TimeSerieType enum.")
            
            if not isinstance(elem["continuity"], bool):
                raise TypeError(f"'{elem}' io 'continuity' is not a boolean.")


        self.__components[name] = component
        
        for time_serie in time_series:
            self.__add_time_serie(name+"_"+time_serie, self.__components[name].time_series[time_serie]["value"])
    
    #@profile
    def get_variables(self) -> dict:
        """Returns the dictionnary that contains the MILP variables.

        Returns
        -------
        dict
            Dictionnary associating the variable name to its associated MILP variable.
        """
        return self.__variables

    #@profile
    def get_results(self, as_dataframe:bool=False) -> pd.DataFrame or dict:
        """Returns the results of the past computations.

        Parameters
        ----------
        as_dataframe : bool, optional
            Returns the results as Dataframe. If False, returns a dictionnary, by default False

        Returns
        -------
        pd.DataFrame or dict
            Results of the past computations
            
        Raises
        ------
        Exception
            Function called before the first solve
        """
        if len(self.__results.columns) == 0:
            raise Exception("No result produced yet, run solve before.")
        
        if as_dataframe:
            return self.__results

        result_dict = {component: {variable:self.__results[component+"_"+variable] \
                                    for variable in self.__variables[component]} \
                                        for component in self.__variables }

        result_dict["time"] = self.__results["time"]
        return result_dict

    #@profile
    def get_components(self) -> dict:
        """Returns the model components list.

        Returns
        -------
        dict
            Dictionnary associating the model components names to their parameters/timeseries.
        """
        return self.__components

    #@profile
    def get_component_io(self, component_name:str) -> Dict[str, Any]:
        """Returns an existing model component Inputs/Outputs from its name.

        Parameters
        ----------
        component_name : str
            Registered component name.

        Returns
        -------
        Dict[str, Any]
            Dict that lists the component Inputs/Outputs and their parameters

        Raises
        ------
        ComponentNameException
            The given component name is not registered.
        """
        if not component_name in self.__components:
            raise ComponentNameException(component_name)

        return self.__components[component_name].io_from_parameters()

    #@profile
    def get_component_time_series(self, component_name:str) -> dict:
        """Returns a component time series from its name.

        Parameters
        ----------
        component_name : str
            Component name for which the time serie definition is requested.

        Returns
        -------
        dict
            Time series definition of the component

        Raises
        ------
        ComponentTypeException
            No component registered at this type.
        """
        if not component_name in self.__components:
            raise ComponentNameException(component_name)

        return self.__components[component_name].time_series

    #@profile
    def get_model(self) -> GenericInterface:
        """Returns the current solver interface.

        Returns
        -------
        GenericInterface
            Currently used solver interface.
        """
        return self.__model

    #@profile
    def define_time_range(self,
        time_step:float,
        time_shift:int,
        future_size:int,
        horizon_count:int):
        """Defines the time properties of the rolling horizon.

        Must only be called once.

        Parameters
        ----------
        time_step : float
            default time step length.
        time_shift : int
            Number of time steps skipped between two horizons.
        future_size : int
            Number of computed time steps in the current horizon.
        horizon_count : int
            Number of horizons computed.

        Raises
        ------
        RuntimeError
            This function was called already.
        """
        if not self.__time_range_defined:
            self.__time_range_defined = True

            self.time_step = time_step
            self.time_shift = time_shift
            self.future_size = future_size
            self.horizon_count = horizon_count

            self.custom_steps = [1 for i in range(future_size)]
        else:
            raise RuntimeError("Time range already defined.")

    #@profile
    def set_custom_steps(self, custom_steps:list):
        """Defines the rolling horizon time steps length.

        Parameters
        ----------
        custom_steps : list
            List of time steps length, if 1, equals the provided **time_step** value.

        Raises
        ------
        ValueError
            Length of custem_steps different from the provided **future_size**.
        UndefinedTimeRangeException
            Function called before *define_time_range*.
        """
        if self.__time_range_defined:
            if len(custom_steps) != self.future_size:
                raise ValueError(f"Given custom steps shall contain {self.future_size} numbers.")
            self.custom_steps = custom_steps
        else:
            raise UndefinedTimeRangeException()

    #@profile
    def __add_time_serie(self, time_serie_name:str, time_serie:pd.DataFrame):
        """Adds a time serie dictionnary to the time series dataframe.

        Parameters
        ----------
        time_serie_name : str
            Name of the time serie
        time_serie : pd.DataFrame
            Time serie dataframe
        """
        if len(self.__time_series.columns) == 0:
            time_serie.set_index("time", inplace=True, drop=False)
            self.__time_series = time_serie
            self.__time_series = self.__time_series.rename(columns={"value":time_serie_name})
        else:
            time_serie.set_index("time", inplace=True)
            time_serie = (time_serie[["value"]]).rename(columns={"value":time_serie_name})

            self.__time_series = pd.concat([self.__time_series, time_serie], axis=1)

    #@profile
    def __interpolate_time_series(self):
        """Interpolates the potential NaN values in the time series dataframe. 
        """
        self.__time_series = self.__time_series.interpolate()

    #@profile
    def create_bus(self, bus_type:str, options:dict):
        """Creates a bus in the model.

        Parameters
        ----------
        bus_type : str
            Bus type, 'bus' is the only valid value.
        options : dict
            Bus parameters, only requests the bus 'name'.

        Raises
        ------
        BusTypeException
            The provided bus type is not registered.
        ParametersException
            The provided parameters are not valid (prints every invalid value).
        """
        if bus_type in self.__component_definition:
            valid_component = True

            for param in self.__component_definition[bus_type]["parameters"]:
                if param in options and isinstance(options[param],\
                    self.__component_definition[bus_type]["parameters"][param]):
                    pass
                else:
                    valid_component = False
                    if not param in options:
                        print(f"Parameter {param} is missing.")
                    elif not isinstance(options[param],\
                        self.__component_definition[bus_type]["parameters"][param]):
                        print(f"Parameter {param} is of the wrong type, found {type(options[param])}")

            if not valid_component:
                raise ParametersException()

            options["component_type"] = bus_type
            options["inputs"] = []
            options["outputs"] = []

            self.__buses[options["name"]] = options
        else:
            raise BusTypeException(bus_type)

    #@profile
    def add_link(self,
        component_1:GenericComponent,
        io_1:str,
        component_2:GenericComponent,
        io_2:str,
        factor:float,
        offset:float):
        """
        Creates a link between two components Input/output.

        The two Input/output are linked with an affine function:

            -   **io_1** \* factor + offset = **io_2** 

        Parameters
        ----------
        component_1 : GenericComponent
            Model component 1 name.
        io_1 : str
            Input/output linked of the first component.
        component_2 : GenericComponent
            Model component 2 name.
        io_2 : str
            Input/output linked of the second component.
        factor : float
            Input/output 2 multiply factor.
        offset : float
            Input/output 2 offset value.
        

        Raises
        ------
        ComponentNameException
            The provided component was not added to the model.
        ComponentNameException
            The provided component was not added to the model.
        ComponentIOException
            Wrong input/output name for given component.
        ComponentIOException
            Wrong input/output name for given component.
        """
        component_name_1 = component_1.name
        component_name_2 = component_2.name

        if not component_name_1 in self.__components:
            raise ComponentNameException(component_name_1)

        if not component_name_2 in self.__components:
            raise ComponentNameException(component_name_2)

        if not io_1 in self.get_component_io(component_name_1):
            raise ComponentIOException(component_name_1, io_1)

        if not io_2 in self.get_component_io(component_name_2):
            raise ComponentIOException(component_name_2, io_2)

        self.__links.append({"component_name_1":component_name_1, 
                                "io_1":io_1, 
                                "component_name_2":component_name_2, 
                                "io_2":io_2, 
                                "factor":factor, 
                                "offset":offset})

    #@profile
    def plug_to_bus(self,
            component:GenericComponent,
            io:str,
            bus_name:str,
            is_input:bool,
            factor:float,
            offset:float):
        """Connects a component Input/output to a bus.

        Parameters
        ----------
        component_1 : GenericComponent
            Model component to plug to the bus.
        io : str
            Input/output linked of the component.
        bus_name : str
            Name of the bus to which the Input/output is linked.
        is_input : bool
            The Input/output is an input of the bus (drives the sign of the Inputs/Outputs).
        factor : float
            Input/output multiply factor.
        offset : float
            Input/output offset value.

        Raises
        ------
        BusNameException
            Given bus name does not exist.
        ComponentNameException
            The provided component was not added to the model.
        ComponentIOException
            Given component does not have the given Input/output.
        """
        component_name_1 = component.name

        if not bus_name in self.__buses:
            raise BusNameException(bus_name)

        if not component_name_1 in self.__components:
            raise ComponentNameException(component_name_1)

        if not io in self.__components[component_name_1].io_from_parameters():
            raise ComponentIOException(component_name_1, io)

        if is_input:
            self.__buses[bus_name]["inputs"].append([component_name_1, io, factor, offset])
        else:
            self.__buses[bus_name]["outputs"].append([component_name_1, io, factor, offset])

    #@profile
    def __interpolate(self, dataframe:pd.DataFrame, times:list, column_name:str) -> np.ndarray:
        """Get the values at the given times of the requested column in a pandas dataframe.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Datafame in which pick the column
        times : list
            Times at which interpolate
        column_name : str
            Column to interpolate name.

        Returns
        -------
        np.ndarray
            _description_
            
        Raises
        ------
        KeyError
            The dataframe doesn't have a 'time' column
        KeyError
            The dataframe doesn't have the requested column
        """
        if not "time" in dataframe.columns:
            raise KeyError("The given dataframe has no column 'time'.")
        if not column_name in dataframe.columns:
            raise KeyError(f"The given dataframe has no column '{column_name}'.")

        return np.interp(times, dataframe["time"], dataframe[column_name])

    #@profile
    def __make_ts_integrated_column(self, column_name:str):
        """Adds to the time series dataframe the integral of a column.

        Parameters
        ----------
        column_name : str
            Column name to integrate.

        Raises
        ------
        KeyError
            The self.__time_series dataframe doesn't have the requested column
        """
        if not column_name in self.__time_series:
            raise KeyError(f"The self.__time_series dataframe has no column '{column_name}'.")

        time_serie = pd.DataFrame()
        time_serie.loc[:, "average_"+column_name] = self.__time_series[column_name].rolling(2, min_periods=1).sum()*0.5

        if "diff_time" not in self.__time_series.columns:
            self.__time_series = pd.concat([self.__time_series, pd.DataFrame({"diff_time":self.__time_series["time"].diff()})], axis=1)
            self.__time_series.loc[0, "diff_time"] = 0.
            
        time_serie.loc[:, "local_integral_"+column_name] = \
            self.__time_series[column_name]*self.__time_series["diff_time"]
        
        time_serie.loc[0, "local_integral_"+column_name] = 0.

        time_serie.loc[:, "integrated_"+column_name] = \
            time_serie["local_integral_"+column_name].cumsum()

        del time_serie["local_integral_"+column_name]
        
        self.__time_series = pd.concat([self.__time_series, time_serie], axis=1)


    #@profile
    def __make_time_steps(self) -> list:
        """Returns the steps times of the current solve.

        Returns
        -------
        list
            List of the current horizon time steps value.

        Raises
        ------
        UndefinedTimeRangeException
            Can't be called before defining time steps
        """
        if not self.__time_range_defined:
            raise UndefinedTimeRangeException()

        return [self.__current_time + sum(self.custom_steps[:i])*self.time_step for i in range(len(self.custom_steps)+1)]


    #@profile
    def __is_it_intensive(self, component_name:str, time_serie:str) -> bool:
        """Returns if the given component time serie is intensive.

        Parameters
        ----------
        component_name : str
            Registered component name.
        time_serie : str
            Component time serie name.

        Returns
        -------
        bool
            Whether the requested time serie is intensive

        Raises
        ------
        ComponentNameException
            Given component name does not exist.
        TimeSerieException
            Given component does not have the given time serie.
        """
        if component_name not in self.__components:
            raise ComponentNameException(component_name)

        if time_serie in self.__components[component_name].get_time_series():
            return self.__components[component_name].get_time_series()[time_serie]["type"] == TimeSerieType.INTENSIVE

        if time_serie in self.get_component_io(component_name):
            return self.get_component_io(component_name)[time_serie]["type"] == TimeSerieType.INTENSIVE

        raise TimeSerieException(self.__components[component_name].__class__.__name__, time_serie)

    #@profile
    def __is_it_extensive(self, component_name:str, time_serie:str) -> bool:
        """Returns if the given component time serie is extensive.

        Parameters
        ----------
        component_name : str
            Registered component name.
        time_serie : str
            Component time serie name.

        Returns
        -------
        bool
            Whether the requested time serie is extensive

        Raises
        ------
        ComponentNameException
            Given component name does not exist.
        TimeSerieException
            Given component does not have the given time serie.
        """
        if component_name not in self.__components:
            raise ComponentNameException(component_name)

        if time_serie in self.__components[component_name].get_time_series():
            return self.__components[component_name].get_time_series()[time_serie]["type"] == TimeSerieType.EXTENSIVE

        if time_serie in self.get_component_io(component_name):
            return self.get_component_io(component_name)[time_serie]["type"] == TimeSerieType.EXTENSIVE

        raise TimeSerieException(self.__components[component_name].__class__.__name__, time_serie)

    #@profile
    def __get_time_serie_extract(self, component_name:str) -> pd.DataFrame:
        """Gets the time series at the current solve time steps of a given component.

        Parameters
        ----------
        component_name : str
            Component of which we want the time series.

        Returns
        -------
        pd.DataFrame
            Requested time series

        Raises
        ------
        RuntimeError
            Can't extract time series before defining time range.
        ComponentNameException
            No component at the given name.
        ValueError
            Internal error : The definition of one of the time serie is neither extensive or intensive.
        """

        ts_extract = {}

        if not self.__time_range_defined:
            raise RuntimeError(f"Can't extract time series before defining time range.")
        if not component_name in self.__components:
            raise ComponentNameException(component_name)

        current_solve_time_steps = self.__make_time_steps()

        for key in self.__components[component_name].get_time_series():
            column_name = component_name+"_"+key

            if not "integrated_"+column_name in self.__time_series:
                self.__make_ts_integrated_column(column_name)

            interpolated_values = self.__interpolate(self.__time_series, current_solve_time_steps, "integrated_"+column_name)

            if self.__is_it_intensive(component_name, key):
                ts_extract[key] = np.diff(interpolated_values)/(np.array(self.custom_steps)*self.time_step)
            elif self.__is_it_extensive(component_name, key):
                ts_extract[key] = np.diff(interpolated_values)
            else:
                raise ValueError(f"Time serie type for {key} of component {self.__components[component_name].__class__.__name__} is not correct.")

        return pd.DataFrame(ts_extract)

    #@profile
    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        Parameters
        ----------
        write_log : bool, optional
            Writes/prints the solving log, by default False

        Raises
        ------
        UndefinedTimeRangeException
            Solve function called before defining the time range.
        """
        self.solve_parameters = solve_parameters

        if self.__steps_solved == 0:
            self.__interpolate_time_series()

        if self.__time_range_defined:
            print("Running first time step")

            self._init_time_step()
            self._solve_time_step()
            self._terminate_time_step()

            for _ in range(0, self.horizon_count - 1):
                print("Running time step", self.__steps_solved+1)
                self.__current_time += sum(self.custom_steps[:self.time_shift])*self.time_step

                self._init_time_step()
                self._solve_time_step()
                self._terminate_time_step()
        else:
            raise UndefinedTimeRangeException()

    #@profile
    def __reset(self):
        """Resets the created MILP model.
        """
        self.__objective = 0.
        self.__variables = {}

        self.create_model_interface()

    #@profile
    def _init_time_step(self):
        """Creates the MILP model from its components definitions."""
        self.__reset()

        if self.__steps_solved > 0:
            line_end = 0

            while self.__results["time"][line_end] < self.__current_time:
                line_end += 1

            old_results = self.__results[:line_end+1]

        for component in self.__components.values():
            time_series = self.__get_time_serie_extract(component.name)

            history = pd.DataFrame()

            if self.__steps_solved > 0:
                for time_serie in self.get_component_io(component.name):
                    if self.get_component_io(component.name)[time_serie]["continuity"]:
                        if len(list(history.columns)) == 0:
                            history["time"] = old_results["time"]

                        history.loc[:, time_serie] = old_results[component.name+"_"+time_serie]

            variables, objective = component.build_model(component.name,
                                                            self.custom_steps,
                                                            time_series,
                                                            history,
                                                            self.__model)

            self.__variables[component.name] = variables
            self.__objective += objective

        for link in self.__links:
            self._create_link(link)

        for bus in self.__buses.values():
            self.__component_definition[bus["component_type"]]["definition"](bus)

        self.__model.set_objective(self.__objective)

    #@profile
    def _solve_time_step(self):
        """Solves the current horizon."""
        self.__model.solve(solve_parameters=self.solve_parameters)

    #@profile
    def _terminate_time_step(self):
        """Terminates the current solved horizon and creates builds the results dataframe."""
        self.__steps_solved += 1
        self._build_results()

    #@profile
    def _create_link(self, link_properties:dict):
        """Creates the constraints of a link between two components Input/Output.

        Parameters
        ----------
        link_properties : dict
            Dictionnary of the link properties, provided in the *add_link* function.
        """

        for i in range(self.future_size):
            coeff_1 = 1.
            coeff_2 = 1.

            if self.__is_it_intensive(link_properties["component_name_1"], link_properties["io_1"]):
                coeff_1 = self.custom_steps[i]

            if self.__is_it_intensive(link_properties["component_name_2"], link_properties["io_2"]):
                coeff_2 = self.custom_steps[i]

            self.__model.add_equality((self.__variables[link_properties["component_name_1"]][link_properties["io_1"]][i]*link_properties["factor"] + link_properties["offset"])*coeff_1, \
                self.__variables[link_properties["component_name_2"]][link_properties["io_2"]][i]*coeff_2)

    #@profile
    def _create_bus(self, bus_properties:dict):
        """Creates the constraints of a bus.

        Parameters
        ----------
        bus_properties : dict
            Bus properties provided while calling the create_bus function.
        """
        for step in range(self.future_size):

            input_coeffs = [self.custom_steps[step] if self.__is_it_intensive(i[0], i[1]) is True else 1. for i in bus_properties["inputs"]]
            output_coeffs = [self.custom_steps[step] if self.__is_it_intensive(o[0], o[1]) is True else 1. for o in bus_properties["outputs"]]

            inputs = [input_coeffs[i]*(self.__variables[bus_properties["inputs"][i][0]][bus_properties["inputs"][i][1]][step]*bus_properties["inputs"][i][2] + bus_properties["inputs"][i][3]) for i in range(len(bus_properties["inputs"]))]
            outputs = [output_coeffs[i]*(self.__variables[bus_properties["outputs"][i][0]][bus_properties["outputs"][i][1]][step]*bus_properties["outputs"][i][2] + bus_properties["outputs"][i][3]) for i in range(len(bus_properties["outputs"]))]

            self.__model.add_equality(self.__model.sum_variables(inputs), self.__model.sum_variables(outputs))

    #@profile
    def _build_results(self):
        """Builds the results dataframe of the last solve."""
        new_df = self.__model.get_results_from_variables(self.__variables)
        new_df.loc[:, "time"] = self.__make_time_steps()[1:]

        if len(list(self.__results.columns)) == 0:
            self.__results = new_df
        else:
            line_end = 0
            while self.__results["time"][line_end] < self.__current_time:
                line_end += 1

            self.__results = pd.concat([self.__results[:line_end+1], new_df], ignore_index=True)

if __name__ == "__main__":
    pass
