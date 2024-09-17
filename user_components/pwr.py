"""EESREP basic nuclear reactor model definitions"""
import pandas as pd

from eesrep.components.generic_component import GenericComponent
from eesrep.eesrep_io import ComponentIO
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_enum import TimeSerieType

class Pwr(GenericComponent):
    """ The EESREP basic nuclear reactor model displays an example of complex machine behavior.
    
    The model takes one input and two outputs:
    
        - power_in : power input, can be linked to a source component.
        - power_out : component energy output.
        - efpd : increments the fuel use.
        
    The behavior of the component is the following: the power of the reactor can be between 
    **p_min** and **p_max**, with an efficiency of **efficiency**.
    
    *power_out* is split in two parts: the main power, constrainted, and the variable power, free of constraints.

    The variable power represents **variable_rate** (from 0 to 1) of the total power.

    The main power is by default at its maximum power. It can lower from **min_time_low** to **max_time_low** time steps 
    to a lower power where it will remain constant. After this time, it will go back to its maximum value for **min_time_100** time steps.

    The power at which the main power can go is discret and defined by **power_steps** equal steps.
    
    The fuel usage is measured in the *efpd* output, starting at **init_efpd** at the first time step."""

    def __init__(self, 
                        name:str,
                        efficiency:float,
                        p_min:float,
                        p_max:float,
                        init_efpd:float,
                        min_time_100:int,
                        min_time_low:int,
                        max_time_low:int,
                        variable_rate:float,
                        power_steps:int):

        self.name = name
        self.efficiency = efficiency
        self.p_min = p_min
        self.p_max = p_max
        self.init_efpd = init_efpd
        self.min_time_100 = min_time_100
        self.min_time_low = min_time_low
        self.max_time_low = max_time_low
        self.variable_rate = variable_rate
        self.power_steps = power_steps

        self.time_series = {}

        self.power_in = ComponentIO(self.name, "power_in", TimeSerieType.INTENSIVE, False)
        self.power_out = ComponentIO(self.name, "power_out", TimeSerieType.INTENSIVE, False)
        self.efpd = ComponentIO(self.name, "efpd", TimeSerieType.INTENSIVE, True)
        self.manoeuver = ComponentIO(self.name, "manoeuver", TimeSerieType.INTENSIVE, True)
        self.power_step = ComponentIO(self.name, "power_step", TimeSerieType.INTENSIVE, True)
    
    def io_from_parameters(self) -> dict:
        """Lists the component variables.

        Returns
        -------
        dict
            Dictionnary listing the variables and their properties, each variable has the two following keys:
                - type (TimeSerieType) : is the variable intensive or extensive
                - continuity (bool) : is the variable given in the next horizons history

        """
        variable_dict = {
                            "power_in": self.power_in,
                            "power_out": self.power_out,
                            "efpd": self.efpd
                        }
        
        if True:
            variable_dict["manoeuver"]= self.manoeuver
            variable_dict["power_step"]= self.power_step

        return variable_dict

    def build_model(self,
        component_name:str,
        time_steps:list,
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
            Dataframe with the variables of previous iterations if "continuity" is at true.
        model_interface : GenericInterface
            Solver interface used to provide the variables
        future : pd.DataFrame
            Dataframe with the previsions of variables of previous iterations if "continuity" is at true.

        """
        objective = 0.
        variables = {}

        #   Variable declarations
        variables["power_in"] = model_interface.get_new_continuous_variable_list(component_name+"_power_in_", len(time_steps), 0., self.p_max/self.efficiency)
        variables["power_out"] = model_interface.get_new_continuous_variable_list(component_name+"_power_out_", len(time_steps), self.p_min, self.p_max)
        
        variables["power_main"] = model_interface.get_new_continuous_variable_list(component_name+"_power_main_", len(time_steps), 0, self.p_max*(1-self.variable_rate))
        variables["power_variable"] = model_interface.get_new_continuous_variable_list(component_name+"_power_variable_", len(time_steps), 0, self.p_max*self.variable_rate)

        # variables["power_change"] = model_interface.get_new_discrete_variable_list(component_name+"_power_change_", len(time_steps), 0, 1)
        
        variables["manoeuver"] = model_interface.get_new_continuous_variable_list(component_name+"_manoeuver_", len(time_steps), 0, 1)

        variables["min_low_time_count"] = model_interface.get_new_continuous_variable_list(component_name+"_min_low_time_count_", len(time_steps), 0, None)
        variables["manoeuver_count"] = model_interface.get_new_continuous_variable_list(component_name+"_manoeuver_count_", len(time_steps), 0, None)
        variables["power_count_100"] = model_interface.get_new_continuous_variable_list(component_name+"_power_count_100_", len(time_steps), 0, None)
        # variables["power_count_feutry8"] = model_interface.get_new_continuous_variable_list(component_name+"_power_count_feutry8_", len(time_steps), 0, None)

        variables["efpd"] = model_interface.get_new_continuous_variable_list(component_name+"_efpd_", len(time_steps), 0., None)

        variables["power_step"] = model_interface.get_new_continuous_variable_list(component_name+"_power_step_", len(time_steps), 0, None)
        variables["manoeuver_change_up"] = model_interface.get_new_discrete_variable_list(component_name+"_manoeuver_change_up_", len(time_steps), 0, 1)
        variables["manoeuver_change_down"] = model_interface.get_new_discrete_variable_list(component_name+"_manoeuver_change_down_", len(time_steps), 0, 1)

        ################


        power_step = self.p_max*(1-self.variable_rate)/self.power_steps

        #   Model definition

        for i in range(len(time_steps)):
            time_step = time_steps[i]

            if i > 0:
                past_manoeuver = variables["manoeuver"][i-1]
            elif len(history) > 0:
                past_manoeuver = history["manoeuver"].iloc[-1]
            else:
                past_manoeuver = 0

            if i > 0:
                past_power_step = variables["power_step"][i-1]
            elif len(history) > 0:
                past_power_step = history["power_step"].iloc[-1]
            else:
                past_power_step = 0

            #   output = input * efficiency
            model_interface.add_equality(model_interface.sum_variables([-variables["power_in"][i]*self.efficiency,
                                                variables["power_out"][i]]), 0)

            #   output = variable part + manoeuvring part
            model_interface.add_equality(model_interface.sum_variables([variables["power_out"][i],
                                                -variables["power_main"][i],
                                                -variables["power_variable"][i]]), 0)

            #   manoeuver power step is smaller than the manoeuvring index*steps count
            model_interface.add_lower_than(model_interface.sum_variables([variables["power_step"][i],
                                                -variables["manoeuver"][i]*self.power_steps]), 0)

            #   a change of manoeuvring index is counted by change up and change down
            model_interface.add_equality(model_interface.sum_variables([variables["manoeuver_change_up"][i],
                                                -variables["manoeuver_change_down"][i],
                                                -variables["manoeuver"][i],
                                                past_manoeuver]), 0)

            #   The main power equals the maximal power minus the manoeuvring power step * power per step
            model_interface.add_equality(model_interface.sum_variables([variables["power_main"][i],
                                                - ( self.p_max*(1-self.variable_rate) - variables["power_step"][i]*power_step )]), 0)

            #   The change in power step is smaller than power step when we are manoeuvering
            model_interface.add_lower_than(model_interface.sum_variables([variables["power_step"][i],
                                                -past_power_step,
                                                -variables["manoeuver_change_up"][i]*self.power_steps]), 0)

            model_interface.add_lower_than(model_interface.sum_variables([-variables["power_step"][i],
                                                past_power_step,
                                                -variables["manoeuver_change_down"][i]*self.power_steps]), 0)

            #   We can't both increase and lower in power
            model_interface.add_lower_than(model_interface.sum_variables([variables["manoeuver_change_down"][i],
                                                variables["manoeuver_change_up"][i]]), 1)


            #   Maximum time at low power
            max_time_low_array = []
            for j in range(self.max_time_low + 1):
                if i-j >= 0:
                    max_time_low_array.append(variables["manoeuver"][i-j])
                elif len(history) > j-i:
                    max_time_low_array.append(history["manoeuver"].iloc[j-i])

            model_interface.add_equality(model_interface.sum_variables([variables["manoeuver_count"][i],
                                                - model_interface.sum_variables(max_time_low_array)]), 0)

            model_interface.add_lower_than(variables["manoeuver_count"][i], self.max_time_low)

            #   Minimum time at low power
            min_time_low_array = []
            for j in range(self.min_time_low + 1):
                if i-j >= 0:
                    min_time_low_array.append(variables["manoeuver"][i-j])
                elif len(history) > j-i:
                    min_time_low_array.append(history["manoeuver"].iloc[j-i])

            model_interface.add_equality(model_interface.sum_variables([variables["min_low_time_count"][i],
                                                - model_interface.sum_variables(min_time_low_array)]), 0)

            model_interface.add_greater_than(model_interface.sum_variables([variables["min_low_time_count"][i],
                                                - self.min_time_low * variables["manoeuver_change_down"][i]]), 0)

            #   Minimum time at 100%
            min_100_time_low_array = []
            for j in range(self.min_time_100 + 1):
                if i-j >= 0:
                    min_100_time_low_array.append(1-variables["manoeuver"][i-j])
                elif len(history) > j-i:
                    min_100_time_low_array.append(1-history["manoeuver"].iloc[j-i])

            model_interface.add_equality(model_interface.sum_variables([variables["power_count_100"][i],
                                                - model_interface.sum_variables(min_100_time_low_array)]), 0)

            model_interface.add_greater_than(model_interface.sum_variables([variables["power_count_100"][i],
                                                - self.min_time_100 * variables["manoeuver_change_up"][i]]), 0)

            #   EFPD counting
            if i > 1:
                past_efpd = variables["efpd"][i-1]
            elif len(history) > 0:
                past_efpd = history["efpd"].iloc[-1]
            else:
                past_efpd = self.init_efpd

            model_interface.add_equality(model_interface.sum_variables([variables["efpd"][i],
                                                - past_efpd,
                                                - variables["power_out"][i]/self.p_max]), 0)
            
        return variables, objective
