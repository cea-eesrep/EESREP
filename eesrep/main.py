"""EESREP model builder and solver module"""

from collections import Counter
import inspect
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from .components.generic_component import GenericComponent
from .components.bus import GenericBus
from .eesrep_exceptions import *
from .eesrep_io import ComponentIO
from .solver_interface.generic_interface import GenericInterface
from .solver_interface.interface_tester import InterfaceTester
from .time_serie_manager import TimeSerieManager

try:
    from .solver_interface.docplex_interface import DocplexInterface
except ImportError:
    class DocplexInterface:
        """ Fake DocplexInterface class for import error management. """
        def __init__(self, direction:str = "Minimize", solver:str = "CPLEX"):
            raise ImportError("Error while importing Docplex Interface. Make sure you have the docplex module installed.")

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

from .eesrep_enum import SolverOption, TimeSerieType

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
        self.__variables: Dict[str, Dict[str, Any]] = {}
        self.__buses: Dict[str, GenericBus] = {}
        self.__results: pd.DataFrame = pd.DataFrame()
        self.__links: List[str, Any, str, Any , float, float] = []

        self.__time_serie_manager: TimeSerieManager = TimeSerieManager()

        self.__current_time: float = 0.
        self.__steps_solved: int = 0

        self.__objective: int = 0.
        self.__cumulated_objective: int = 0.
        self.__objective_io_list: List[Tuple[ComponentIO, float]] = []

        self.__time_range_defined: bool = False

        self.time_step: float = -1
        self.time_shift: int = -1
        self.future_size: int = -1
        self.horizon_count: int = -1
        self.__solved_horizons: int = 0
        self.custom_steps: List[float] = []
        self.solve_parameters: dict = {}
        self.__path_intermediary_results: str = ""

        self.__post_processing:Callable[[pd.DataFrame], pd.DataFrame] = None

    #@profile
    def create_model_interface(self):
        """
            Creates the model interface object from the solver name.

            Raises
            ------
                ValueError: The solver argument provided while creating an Eesrep object is not correct.
        """
        if self.__interface.lower() not in ["mip", "docplex", "pyomo"] + list(self.__custom_interfaces.keys()):
            raise ValueError(
                f"Interface name {self.__interface} is not implemented, please use: mip, pyomo, docplex or register your interface first.")

        if self.__interface in self.__custom_interfaces:
            self.__model = self.__custom_interfaces[self.__interface](direction = self.__direction , solver = self.__solver)

        elif self.__interface.lower() == "mip":
            self.__model = MIPInterface(direction = self.__direction , solver = self.__solver)

        elif self.__interface.lower() == "docplex":
            self.__solver = "CPLEX"
            self.__model = DocplexInterface(direction = self.__direction)

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
        if interface_name in self.__custom_interfaces or interface_name.lower() in ["cbc", "gurobi", "docplex", "pyomo"]:
            raise ValueError(f"A custom interface already exists at the key '{interface_name}'")

        tester = InterfaceTester()

        tester.test(interface)

        self.__custom_interfaces[interface_name] = interface

        self.__interface = interface_name

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

        if isinstance(component, GenericBus):
            if name in self.__buses:
                raise ValueError(f"Bus {name} already exists.")
        else:
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
            if not isinstance(elem, ComponentIO):
                raise TypeError(f"'{elem}' io definition is not a ComponentIO object.")

        if "\ " in name:
            print("/!\\ Space caracter present in the component name, please replace to underscore /!\\")

        if "-" in name:
            print("/!\\ Dash caracter present in the component name, please replace to underscore /!\\")

        if isinstance(component, GenericBus):
            self.__buses[name] = component
        else:
            self.__components[name] = component
        
        for time_serie in time_series:
            self.__time_serie_manager.add_time_serie(name+"_"+time_serie, 
                                                     self.__components[name].time_series[time_serie]["value"],
                                                     self.__is_it_intensive(name, time_serie))
    
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

    def get_objective_value(self) -> float:
        """Returns the cumulated value of the objective.

        Warning: if several horizons were solved, it returns the sum of the horizons objectives, 
        this function does not cut the horizons overlaps

        Returns
        -------
        float
            Objective value of the model
        """
        if self.__solved_horizons > 1 and self.time_shift < self.future_size:
            print("/!\\ Several horizons were solved, the horizons overlaps contribution to objective are not removed /!\\")
            
        return self.__cumulated_objective

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
    def get_component_io(self, component_name:str) -> Dict[str, ComponentIO]:
        """Returns an existing model component Inputs/Outputs from its name.

        Parameters
        ----------
        component_name : str
            Registered component name.

        Returns
        -------
        Dict[str, ComponentIO]
            Dict that lists the component Inputs/Outputs

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
    def add_link(self,
        io_1:ComponentIO,
        io_2:ComponentIO,
        factor:float,
        offset:float):
        """
        Creates a link between two components Input/output.

        The two Input/output are linked with an affine function:

            -   **io_1** \* factor + offset = **io_2** 

        Parameters
        ----------
        io_1 : ComponentIO
            Input/output linked of the first component.
        io_2 : ComponentIO
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
        component_name_1 = io_1.component_name
        component_name_2 = io_2.component_name

        if not component_name_1 in self.__components:
            raise ComponentNameException(component_name_1)

        if not component_name_2 in self.__components:
            raise ComponentNameException(component_name_2)

        if not io_1.io_name in self.get_component_io(component_name_1):
            raise ComponentIOException(component_name_1, io_1.io_name)

        if not io_2.io_name in self.get_component_io(component_name_2):
            raise ComponentIOException(component_name_2, io_2.io_name)

        self.__links.append({"component_name_1":component_name_1, 
                                "io_1":io_1.io_name, 
                                "component_name_2":component_name_2, 
                                "io_2":io_2.io_name, 
                                "factor":factor, 
                                "offset":offset})

    #@profile
    def plug_to_bus(self,
            io:ComponentIO,
            bus_io:ComponentIO,
            factor:float,
            offset:float):
        """Connects a component Input/output to a bus.

        Parameters
        ----------
        io : str
            Input/output of the component.
        io : str
            Input/output of the bus to plug to.
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
        component_name_1 = io.component_name
        bus_name = bus_io.component_name

        if not bus_name in self.__buses:
            raise BusNameException(bus_name)

        if not component_name_1 in self.__components:
            raise ComponentNameException(component_name_1)

        if not io.io_name in self.__components[component_name_1].io_from_parameters():
            raise ComponentIOException(component_name_1, io.io_name)

        if bus_io.io_name == "input":
            self.__buses[bus_name].inputs.append([io, factor, offset])
        else:
            self.__buses[bus_name].outputs.append([io, factor, offset])

    def add_io_to_objective(self, io:ComponentIO, price:float=0.):
        """Adds a component input/output to the objective at a given price

        Parameters
        ----------
        io : ComponentIO
            Input/output to add to the objective
        price : float, optional
            Price per unit of the input/output, by default 0.

        Raises
        ------
        ComponentNameException
            No component at this name in the model
        ComponentIOException
            No such IO name for the given component name
        """        
        if not io.component_name in self.__components:
            raise ComponentNameException(io.component_name)

        if not io.io_name in self.__components[io.component_name].io_from_parameters():
            raise ComponentIOException(io.component_name, io.io_name)

        if price != 0.:
            self.__objective_io_list.append((io, price))
        

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
            return self.get_component_io(component_name)[time_serie].type == TimeSerieType.INTENSIVE

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
            return self.get_component_io(component_name)[time_serie].type == TimeSerieType.EXTENSIVE

        raise TimeSerieException(self.__components[component_name].__class__.__name__, time_serie)

    #@profile
    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        Parameters
        ----------
        write_log : bool, optional
            Writes/prints the solving log, by default False

        Raises
        ------
        ValueError
            Provided path for intermediate result file leads to an unexisting folder.
        UndefinedTimeRangeException
            Solve function called before defining the time range.
        """
        self.solve_parameters = solve_parameters

        if SolverOption.INTERMEDIATE_RESULTS_PATH in self.solve_parameters.keys():
            if not os.path.isdir(Path(self.solve_parameters[SolverOption.INTERMEDIATE_RESULTS_PATH]).absolute().parent):
                raise ValueError("Provided intermediate result file parent folder does not exist.")
                
            self.__path_intermediary_results = self.solve_parameters[SolverOption.INTERMEDIATE_RESULTS_PATH]

            #   Removing the parameter as it is not supposed to be given to the solver_intefaces
            del solve_parameters[SolverOption.INTERMEDIATE_RESULTS_PATH]

        if self.__steps_solved == 0:
            self.__time_serie_manager.interpolate_time_series()

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
        self.__solved_horizons = 0
        self.__variables = {}

        self.create_model_interface()

    #@profile
    def _init_time_step(self):
        """Creates the MILP model from its components definitions."""
        self.__reset()
            
        current_solve_time_steps = self.__make_time_steps()

        if self.__steps_solved > 0:
            line_end = 0

            while self.__results["time"][line_end] < self.__current_time:
                line_end += 1

            old_results = self.__results[:line_end+1]
            old_future_results = self.__results.iloc[line_end:]
            
            intensive_dict = {f"{c}_{io}":self.__components[c].io_from_parameters()[io].type == TimeSerieType.INTENSIVE for c in self.__components for io in self.__components[c].io_from_parameters()}
            
            future_manager = TimeSerieManager(time_serie_data=old_future_results, 
                                                intensives=intensive_dict, 
                                                is_future=True)

        #   Initialising each component
        for component in self.__components.values():
            component_time_series = self.__time_serie_manager.get_time_serie_extract(current_solve_time_steps, component)

            #   Loading the results of previous horizons
            if self.__steps_solved > 0:
                history = {}

                for time_serie in self.get_component_io(component.name):
                    if self.get_component_io(component.name)[time_serie].continuity:
                        if len(list(history)) == 0:
                            history["time"] = old_results["time"]

                        history[time_serie] = old_results[component.name+"_"+time_serie]

                future = future_manager.get_time_serie_extract(current_solve_time_steps[:-1], component, if_continuity=True)
            else:
                history = {}
                future = pd.DataFrame()

            #   Building the model for each component
            variables, objective = component.build_model(component.name,
                                                            self.custom_steps,
                                                            component_time_series,
                                                            pd.DataFrame(history),
                                                            self.__model, 
                                                            future = future)

            self.__variables[component.name] = variables
            self.__objective = self.__model.sum_variables([self.__objective, objective])

        #   Mutualising the objectives of each component 
        for io_ in self.__objective_io_list:
            objective = self.__model.sum_variables([io_[1]*var for var in self.__variables[io_[0].component_name][io_[0].io_name]])
            self.__objective = self.__model.sum_variables([self.__objective, objective])

        #   Creating links
        for link in self.__links:
            self._create_link(link)

        #   Creating buses
        for bus in self.__buses.values():
            self._create_bus(bus)

        self.__model.set_objective(self.__objective)

    #@profile
    def _solve_time_step(self):
        """Solves the current horizon."""
        self.__model.solve(solve_parameters=self.solve_parameters)

    #@profile
    def _terminate_time_step(self):
        """Terminates the current solved horizon and creates builds the results dataframe. If a post-processing function was provided, it is run afterward.

        Raises
        ------
        PostProcessingException
            Any exception occured during the post-processing.
        PostProcessingException
            The result dataframe length changed.
        PostProcessingException
            The result dataframe columns names changed.
        """
        self.__steps_solved += 1
        self._build_results()

        if self.__post_processing is not None:
            print(f"Running provided post-processing function.")
            save_len_results:int = len(self.__results)

            save_keys_results:List[str] = list(self.__results.keys())
            save_keys_results.sort()

            try:
                self.__results = self.__post_processing(self.__results)
            except Exception as e:
                raise PostProcessingException(f"{type(e).__name__} – {e}")
            
            if len(self.__results) != save_len_results:
                raise PostProcessingException(f"The number of lines in the result dataframe changed from {save_len_results} to {len(self.__results)}.")
            
            new_keys_results:List[str] = list(self.__results.keys())
            new_keys_results.sort()

            if new_keys_results != save_keys_results:
                raise PostProcessingException(f"The result dataframe columns names changed during the post-processing.")
    
        self.__cumulated_objective += self.__model.get_result_objective()

        if self.__path_intermediary_results != "":
            print(f"Writing results of horizon {self.__steps_solved} to file {self.__path_intermediary_results}")

            self.__results.to_csv(self.__path_intermediary_results)

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
    def _create_bus(self, bus:GenericBus):
        """Creates the constraints of a bus.

        Parameters
        ----------
        bus_properties : dict
            Bus properties provided while calling the create_bus function.
        """
        for step in range(self.future_size):
            input_coeffs = [self.custom_steps[step] if self.__is_it_intensive(i[0].component_name, i[0].io_name) else 1. for i in bus.inputs]
            output_coeffs = [self.custom_steps[step] if self.__is_it_intensive(o[0].component_name, o[0].io_name) else 1. for o in bus.outputs]

            inputs = [input_coeffs[i]*(self.__variables[bus.inputs[i][0].component_name][bus.inputs[i][0].io_name][step]*bus.inputs[i][1] + bus.inputs[i][2]) 
                            for i in range(len(bus.inputs))]
            
            outputs = [output_coeffs[i]*(self.__variables[bus.outputs[i][0].component_name][bus.outputs[i][0].io_name][step]*bus.outputs[i][1] + bus.outputs[i][2]) 
                            for i in range(len(bus.outputs))]

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

    def set_post_processing(self, f:Callable) -> None:
        """Sets a post porcessing function to be called at the end of every rolling horizon.

        Parameters
        ----------
        f : Callable
            Post-processing function

        Raises
        ------
        RuntimeError
            A function was already defined.
        TypeError
            The provided argument is not a callable function
        AssertionError
            The provided function does not have one argument.
        """
        if self.__post_processing is not None:
            raise RuntimeError("Post-processing function already defined.")

        if not callable(f):
            raise TypeError(f"Input must be a callable, found {type(f)}")
        
        assert len(inspect.getfullargspec(f).args) == 1, "Post-processing function must have only one input, which must be a panda DataFrame."

        self.__post_processing = f

if __name__ == "__main__":
    pass
