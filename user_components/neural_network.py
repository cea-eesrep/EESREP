"""This file contains the EESREP generic neural network model."""
import os
import pandas as pd

from eesrep.components.generic_component import GenericComponent
from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_enum import TimeSerieType

class NeuralNetwork(GenericComponent):
    """EESREP Neural network component definition. 
    
    This component can be used to model complex/non-linear behavior but is computationally heavy.

    The neural network has the following parameters:

        - inputs_count : amount of inputs of the neural network.
        - outputs_count : amount of outputs of the neural nework.
        - max_value : maximum expected value of a neuron, bounding the value properly can help the resolution.
        - neuron_definition_path : path to the csv file containing the weights/bias.
    
    The activation function is strictly limited to ReLu.
    
    A python script to extract the csv file from a tensorflow model is given in comment here."""

    def __init__(self, name:str,
                        inputs_count:int,
                        outputs_count:int,
                        max_value: float,
                        neuron_definition_path:str):
        """  Creates a neural network component

        Parameters
        ----------
        name : str
            Name of the component
        inputs_count : int
            amount of inputs of the neural network.
        outputs_count : int
            amount of outputs of the neural nework.
        max_value : float
            maximum expected value of a neuron, bounding the value properly can help the resolution.
        neuron_definition_path : str
            path to the csv file containing the weights/bias.
        """                        
        self.name = name
        self.inputs_count = inputs_count
        self.outputs_count = outputs_count
        self.max_value = max_value
        self.neuron_definition_path = neuron_definition_path

        self.time_series = {}

        for io in self.io_from_parameters():
            setattr(self, io, io)

    def io_from_parameters(self) -> dict:
        """Lists the component variables.

        Returns
        -------
        dict
            Dictionnary listing the variables and their properties, each variable has the two following keys:
                - type (TimeSerieType) : is the variable intensive or extensive
                - continuity (bool) : is the variable given in the next horizons history

        """
        variable_dict = {}

        for i in range(self.inputs_count):
            variable_dict[f"input_{i}"] = {
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity":False
                                        }

        for i in range(self.outputs_count):
            variable_dict[f"output_{i}"] = {
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity":False
                                        }

        return variable_dict

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

        if not os.path.isfile(self.neuron_definition_path):
            raise ValueError("No file found at "+self.neuron_definition_path)

        objective = 0.
        variables = {}

        neuron_definition = pd.read_csv(self.neuron_definition_path, sep=";")
        deep_layers_count = neuron_definition["RN.NeuronsPerLayer"].astype(bool).sum(axis=0)

        ###     Creating variables
        for input_id in range(self.inputs_count):
            variables[f"input_{input_id}"] = model_interface.get_new_continuous_variable_list(f"{component_name}_input_{input_id}", len(time_steps), None, None)

        for output in range(self.outputs_count):
            variables[f"output_{output}"] = model_interface.get_new_continuous_variable_list(f"{component_name}_output_{output}_value", len(time_steps), None, None)

        for deep_layer in range(deep_layers_count):
            for neuron in range(neuron_definition["RN.NeuronsPerLayer"].loc[deep_layer]):
                current_neuron_name = f"deep_{deep_layer}_{neuron}"
                variables[f"{current_neuron_name}_value"] = model_interface.get_new_continuous_variable_list(f"{component_name}_{current_neuron_name}_value", len(time_steps), None, None)
                variables[f"{current_neuron_name}_relu_plus"] = model_interface.get_new_continuous_variable_list(f"{component_name}_{current_neuron_name}_relu_plus", len(time_steps), 0., None)
                variables[f"{current_neuron_name}_relu_minus"] = model_interface.get_new_continuous_variable_list(f"{component_name}_{current_neuron_name}_relu_minus", len(time_steps), 0., None)
                variables[f"{current_neuron_name}_relu_positive"] = model_interface.get_new_discrete_variable_list(f"{component_name}_{current_neuron_name}_relu_positive", len(time_steps), 0, 1)


        ###     Creating constraints
        for time in range(0, len(time_steps)):
            past_layer_width = self.inputs_count
            last_layer = "input"
            neuron_id = 0
            neural_link = 0
            for deep_layer in range(deep_layers_count):
                for neuron in range(neuron_definition["RN.NeuronsPerLayer"].loc[deep_layer]):
                    current_neuron_name = f"deep_{deep_layer}_{neuron}"

                    past_neuron_sum = [-neuron_definition["RN.Bias"].loc[neuron_id]]

                    for past_neuron in range(past_layer_width):
                        past_neuron_name = f"{last_layer}_{past_neuron}"

                        if last_layer == "input":
                            past_neuron_sum.append(-variables[f"{past_neuron_name}"][time] * neuron_definition["RN.Coeffs"].loc[neural_link])
                        else:
                            past_neuron_sum.append(-variables[f"{past_neuron_name}_relu_plus"][time] * neuron_definition["RN.Coeffs"].loc[neural_link])

                        neural_link += 1

                    model_interface.add_equality(model_interface.sum_variables([variables[f"{current_neuron_name}_value"][time]]+
                                                                past_neuron_sum), 0)

                    model_interface.add_equality(model_interface.sum_variables([variables[f"{current_neuron_name}_value"][time],
                                                        - variables[f"{current_neuron_name}_relu_plus"][time],
                                                        variables[f"{current_neuron_name}_relu_minus"][time]]) ,0)

                    model_interface.add_lower_than(model_interface.sum_variables([variables[f"{current_neuron_name}_relu_plus"][time],
                                                        - variables[f"{current_neuron_name}_relu_positive"][time] * self.max_value]) ,0)

                    model_interface.add_lower_than(model_interface.sum_variables([variables[f"{current_neuron_name}_relu_minus"][time],
                                                        (variables[f"{current_neuron_name}_relu_positive"][time] - 1.) * self.max_value]) ,0)

                    neuron_id += 1

                last_layer = f"deep_{deep_layer}"
                past_layer_width = neuron_definition["RN.NeuronsPerLayer"].loc[deep_layer]

            for output in range(self.outputs_count):
                current_neuron_name = f"output_{output}"
                past_neuron_sum = [-neuron_definition["RN.Bias"].loc[neuron_id]]

                for past_neuron in range(past_layer_width):
                    past_neuron_name = f"{last_layer}_{past_neuron}"

                    if last_layer == "input":
                        past_neuron_sum.append(-variables[f"{past_neuron_name}"][time] * neuron_definition["RN.Coeffs"].loc[neural_link])
                    else:
                        past_neuron_sum.append(-variables[f"{past_neuron_name}_relu_plus"][time] * neuron_definition["RN.Coeffs"].loc[neural_link])

                    neural_link += 1

                model_interface.add_equality(model_interface.sum_variables([variables[f"{current_neuron_name}"][time]]+
                                                            past_neuron_sum), 0)

                neuron_id += 1

        return variables, objective

# The coefficient table can be obtained from a Tensorflow model using the following python script:
#
#     RN_name = "RN"
#
#     bias_list = []
#     weights_list = []
#
#     for i in range(len(hidden_nodes)+1):
#         for bias in constraints_container.trainable_weights[2*i+1].numpy():
#             bias_list.append(bias)
#
#         for weights in constraints_container.trainable_weights[2*i].numpy().transpose():
#             for weight in weights:
#                 weights_list.append(weight)
#
#     output_file = open("RN_coeffs.csv", "w+")
#     output_file.write(RN_name+".NeuronsPerLayer;"+RN_name+".Bias;"+RN_name+".Coeffs;\n")
#
#     for i in range(len(weights_list)):
#         if i < len(hidden_nodes):
#             neuron_count = hidden_nodes[i]
#         else:
#             neuron_count = 0
#
#         if i < len(bias_list):
#             bias = bias_list[i]
#         else:
#             bias = 0.
#
#         output_file.write(str(neuron_count)+";"+str(bias)+";"+str(weights_list[i])+";\n")
#
#     output_file.close()
#
#
# The csv file generated can then be used as datafile in the component. This way, only the input output and layers count need to be defined in the json/ini files.
