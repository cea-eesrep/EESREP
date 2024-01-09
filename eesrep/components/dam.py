"""This file contains the EESREP generic dam model."""
import pandas as pd

from eesrep.components.generic_component import GenericComponent
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_enum import TimeSerieType

def check_ts(name: str, ts : pd.DataFrame):
    if not ts.empty:
        if not "time" in ts.columns:
            raise KeyError(f"Column time absent from the {name} parameter.")
        
        if not "value" in ts.columns:
            raise KeyError(f"Column value absent from the {name} parameter.")
        return True
    else:
        return False

class Dam(GenericComponent):
    """EESREP dam component models a basic dam behavior. All inputs and outputs are given in the same unit.
    
    It has the following inputs/outputs:

        -   power_in : free input, that can be plugged to another component output (can be used for dam chain).
        -   water_inflow : fatal water inflow.
        -   power_pump : water pumped from another model variable (equivalent with power_in, but constrainted).
        -   power_free : free power output (can be used for non-turbined output).

    The dam storage is stored in the variable 'storage'.

    The dam is defined with the following parameters:
    
        -   efficiency : loss in the power output.
        -   p_min : power_out minimum value
        -   p_max : power_out maximum value
        -   max_storage : maximum storage value
        -   init_storage : storage value at the first horizon first time step (normalised with max_storage)
        -   pump_max : maximum pumping power (pump disabled if 0)
        -   pump_efficiency : loss in the pumping input
        -   free_output : activates the power_free output
        -   power_input : adds a secondary input, optimised in the model
        -   difference_from_limit_price : adds to the objective :
                price * abs(storage out of [variable_storage_min*max_storage, variable_storage_max*max_storage])
        -   difference_from_average_price : adds to the objective :
                price * abs(storage - variable_storage_average*max_storage)
        """
    def __init__(self,
                    name:str,
                    efficiency:float,
                    p_min:float,
                    p_max:float,
                    max_storage:float,
                    init_storage:float,
                    pump_max:float,
                    pump_efficiency:float,
                    free_output:bool,
                    power_input:bool,
                    difference_from_limit_price:float,
                    difference_from_average_price:float,
                    run_of_river : pd.DataFrame = pd.DataFrame(),
                    water_inflow : pd.DataFrame = pd.DataFrame(),
                    variable_storage_min : pd.DataFrame = pd.DataFrame(),
                    variable_storage_average : pd.DataFrame = pd.DataFrame(),
                    variable_storage_max : pd.DataFrame = pd.DataFrame()):
        """Instanciates a Dam component to provide to EESREP.

        Parameters
        ----------
        name : str
            Name of the dam
        efficiency : float
            Loss in the power output
        p_min : float
            Minimum operating power
        p_max : float
            Maximum operating power
        max_storage : float
            Storage capacity
        init_storage : float
            storage value at the first horizon first time step (normalised with max_storage)
        pump_max : float
            maximum pumping power (pump disabled if 0)
        pump_efficiency : float
            loss in the pumping input
        free_output : bool
            activates the power_free output
        power_input : bool
            adds a secondary input, optimised in the model
        difference_from_limit_price : float
            Price per storage unit out of bounds
        difference_from_average_price : float
            Price for the difference between the storage and average at the last time step
        run_of_river : pd.DataFrame, optional
            Time serie defining a variable minimal power, by default pd.DataFrame()
        water_inflow : pd.DataFrame, optional
            Time serie defining the dam inflow power, by default pd.DataFrame()
        variable_storage_min : pd.DataFrame, optional
            Time serie defining a variable minimum storage bound, by default pd.DataFrame()
        variable_storage_average : pd.DataFrame, optional
            Time serie defining a variable average storage bound, by default pd.DataFrame()
        variable_storage_max : pd.DataFrame, optional
            Time serie defining a variable maximum storage bound, by default pd.DataFrame()
        """          
        self.name = name
        self.efficiency = efficiency
        self.p_min = p_min
        self.p_max = p_max
        self.max_storage = max_storage
        self.init_storage = init_storage
        self.pump_max = pump_max
        self.pump_efficiency = pump_efficiency
        self.free_output = free_output
        self.power_input = power_input
        self.difference_from_limit_price = difference_from_limit_price
        self.difference_from_average_price = difference_from_average_price

        self.time_series = {}

        if check_ts("run_of_river", run_of_river):
            self.time_series["run_of_river"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": run_of_river
                                            }

        if check_ts("water_inflow", water_inflow):
            self.time_series["water_inflow"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": water_inflow
                                            }
                                            
        if check_ts("variable_storage_min", variable_storage_min):
            self.time_series["variable_storage_min"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": variable_storage_min
                                            }

        if check_ts("variable_storage_average", variable_storage_average):
            self.time_series["variable_storage_average"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": variable_storage_average
                                            }

        if check_ts("variable_storage_max", variable_storage_max):
            self.time_series["variable_storage_max"]={
                                                "type": TimeSerieType.INTENSIVE,
                                                "value": variable_storage_max
                                            }

        self.power_in = "power_in"
        self.power_out = "power_out"
        self.storage = "storage"
        self.power_pump = "power_pump"
        self.power_free = "power_free"

    def io_from_parameters(self) -> dict:
        """Lists the component Input/Outputs.

        Returns
        -------
        dict
            Dictionnary listing the Input/Outputs and their properties, each Input/Output has the two following keys:
                - type (TimeSerieType) : is the Input/Output intensive or extensive
                - continuity (bool) : is the Input/Output given in the next horizons history

        """
        io_dict = {
                            "power_in":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity":False
                                        },
                            "power_out":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity":False
                                        },
                            "storage":{
                                            "type": TimeSerieType.EXTENSIVE,
                                            "continuity":True
                                        }
                        }

        if self.pump_max > 0:
            io_dict["power_pump"] = {
                                                "type": TimeSerieType.INTENSIVE,
                                                "continuity":False
                                            }

        if self.free_output:
            io_dict["power_free"] = {
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity":False
                                        }

        return io_dict

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
        objective_list = []
        variables = {}

        #   Variable declarations
        if self.power_input:
            variables["power_in"] = model_interface.get_new_continuous_variable_list(component_name+"_power_in_", len(time_steps), 0., None)
        else:
            variables["power_in"] = [0.]*len(time_steps)
        
        variables["power_out"] = model_interface.get_new_continuous_variable_list(component_name+"_power_out_", len(time_steps), self.p_min, self.p_max)

        variables["storage"] = model_interface.get_new_continuous_variable_list(component_name+"_storage_", len(time_steps), 0., self.max_storage)

        if self.free_output:
            variables["power_free"] = model_interface.get_new_continuous_variable_list(component_name+"_power_free_", len(time_steps), 0, None)

        if self.pump_max:
            variables["power_pump"] = model_interface.get_new_continuous_variable_list(component_name+"_power_pump_", len(time_steps), 0., self.pump_max)

        if self.difference_from_limit_price > 0 and "variable_storage_max" in time_series:
            variables["difference_to_top_plus"] = model_interface.get_new_continuous_variable_list(component_name+"_difference_to_top_plus_", len(time_steps), 0., None)
            variables["difference_to_top_minus"] = model_interface.get_new_continuous_variable_list(component_name+"_difference_to_top_minus_", len(time_steps), 0., None)

        if self.difference_from_limit_price > 0 and "variable_storage_min" in time_series:
            variables["difference_to_bottom_plus"] = model_interface.get_new_continuous_variable_list(component_name+"_difference_to_bottom_plus_", len(time_steps), 0., None)
            variables["difference_to_bottom_minus"] = model_interface.get_new_continuous_variable_list(component_name+"_difference_to_bottom_minus_", len(time_steps), 0., None)

        if self.difference_from_average_price > 0 and "variable_storage_average" in time_series:
            variables["final_difference_to_average_plus"] = model_interface.get_new_continuous_variable(component_name+"_final_difference_to_average_plus_0", 0., None)
            variables["final_difference_to_average_minus"] = model_interface.get_new_continuous_variable(component_name+"_final_difference_to_average_minus_0", 0., None)


        #   Model definition
        if len(history) > 0:
            power_init = history["storage"].loc[len(history)-1]
        else:
            power_init = self.max_storage * self.init_storage

        for i in range(len(time_steps)):
            time_step = time_steps[i]
            #   Storage bounds
            if "variable_storage_min" in time_series:
                min_storage = self.max_storage * time_series["variable_storage_min"][i]
            else:
                min_storage = 0.

            if "variable_storage_max" in time_series:
                max_storage = self.max_storage * time_series["variable_storage_max"][i]
            else:
                max_storage = self.max_storage

            if self.difference_from_limit_price > 0 and "variable_storage_max" in time_series:
                
                model_interface.add_equality(model_interface.sum_variables([variables["storage"][i],
                                                    -max_storage,
                                                    -variables["difference_to_top_plus"][i],
                                                    variables["difference_to_top_minus"][i]]), 0)

                objective_list.append(self.difference_from_limit_price * variables["difference_to_top_plus"][i])
            else:
                model_interface.add_lower_than(variables["storage"][i], max_storage)

            if self.difference_from_limit_price > 0 and "variable_storage_min" in time_series:
                model_interface.add_equality(model_interface.sum_variables([variables["storage"][i],
                                                    -min_storage,
                                                    -variables["difference_to_bottom_plus"][i],
                                                    variables["difference_to_bottom_minus"][i]]), 0)

                objective_list.append(self.difference_from_limit_price * variables["difference_to_top_plus"][i])

                objective_list.append(self.difference_from_limit_price * variables["difference_to_bottom_minus"][i])
            else:
                model_interface.add_greater_than(variables["storage"][i], min_storage)


            #   Adds pump if max power greater than 0
            if self.pump_max > 0:
                pump_variable = variables["power_pump"][i]*self.pump_efficiency
            else:
                pump_variable = 0.

            if "water_inflow" in time_series:
                inflow = time_series["water_inflow"][i]
            else:
                inflow = 0.

            #   Adds free output if exists
            if self.free_output > 0:
                free_variable = variables["power_free"][i]
            else:
                free_variable = 0.

            if i == 0:
                past_storage = power_init
            else:
                past_storage = variables["storage"][i-1]


            #   Mass conservation
            model_interface.add_equality(model_interface.sum_variables([-variables["power_in"][i]*time_step,
                                                variables["power_out"][i]*time_step/self.efficiency,
                                                free_variable*time_step,
                                                -pump_variable*time_step,
                                                -inflow*time_step,
                                                variables["storage"][i],
                                                -past_storage]), 0)

            if "run_of_river" in time_series:
                model_interface.add_greater_than(model_interface.sum_variables([variables["power_out"][i], free_variable]), time_series["run_of_river"].loc[i])


        if self.difference_from_average_price > 0. and "variable_storage_average" in time_series:
            model_interface.add_equality(model_interface.sum_variables([variables["storage"][-1],
                                                -time_series["variable_storage_average"].loc[len(time_series)-1]*self.max_storage,
                                                -variables["final_difference_to_average_plus"],
                                                variables["final_difference_to_average_minus"]]), 0)

            objective_list.append(self.difference_from_average_price * (variables["final_difference_to_average_plus"] + variables["final_difference_to_average_minus"]))


        return variables, model_interface.sum_variables(objective_list)
