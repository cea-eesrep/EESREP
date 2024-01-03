"""Module providing an interface between Eersep and the mip module."""

import mip
import pandas as pd
import numpy as np

from eesrep.eesrep_exceptions import *

class MIPInterface():
    """Interface class between the python MIP module and Esreep."""

    def __init__(self, direction="minimize", solver="CBC"):
        """Initialises the inteface object, and stores the direction and solver for later use.
        
        Parameters
        ----------
        direction : str, optional
            Direction in which the objective must be optimised, can be Minimize or Maximize, by default "Minimize"
        solver : str, optional
            Solver used by the module, by default "CPLEX" if available
        """
        if direction.lower() == "minimize":
            self.__direction = mip.MINIMIZE
        else:
            self.__direction = mip.MAXIMIZE

        self.__solver = solver

        self.__model = mip.Model(
            sense=self.__direction, solver_name=self.__solver)

    def get_new_continuous_variable(
        self,
        name:str,
        min_value:float,
        max_value:float):
        """Returns a continuous variable created by the solver module.

        Parameters
        ----------
        name : str
            Name of the variable
        min_value : float
            Variable minimal value
        max_value : float
            Variable maximal value
        """
        if max_value is None and min_value is None:
            return self.__model.add_var(var_type=mip.CONTINUOUS, name=name)
        elif max_value is None:
            return self.__model.add_var(var_type=mip.CONTINUOUS, lb=min_value, name=name)
        elif min_value is None:
            return self.__model.add_var(var_type=mip.CONTINUOUS, ub=max_value, name=name)
        else:
            return self.__model.add_var(var_type=mip.CONTINUOUS, lb=min_value, ub=max_value, name=name)

    def get_new_discrete_variable(self,
        name:str,
        min_value:float,
        max_value:float):
        """Returns a discrete variable created by the solver module.

        Parameters
        ----------
        name : str
            Name of the variable
        min_value : float
            Variable minimal value
        max_value : float
            Variable maximal value
        """
        if max_value is None and min_value is None:
            return self.__model.add_var(var_type=mip.INTEGER, name=name)
        elif max_value is None:
            return self.__model.add_var(var_type=mip.INTEGER, lb=min_value, name=name)
        elif min_value is None:
            return self.__model.add_var(var_type=mip.INTEGER, ub=max_value, name=name)
        else:
            return self.__model.add_var(var_type=mip.INTEGER, lb=min_value, ub=max_value, name=name)

    def get_new_continuous_variable_list(self,
        base_name:str,
        count:int,
        min_value:float,
        max_value:float):
        """Returns a list of continuous variables created by the solver module.

        Parameters
        ----------
        base_name : str
            Name prefix of the variables
        count : int
            Number of requested variables
        min_value : float
            Variables minimal value
        max_value : float
            Variables maximal value
        """
        return [self.get_new_continuous_variable(base_name+str(i), min_value, max_value) for i in range(count)]

    def get_new_discrete_variable_list(self,
        base_name:str,
        count:int,
        min_value:float,
        max_value:float):
        """Returns a list of discrete variables created by the solver module.

        Parameters
        ----------
        base_name : str
            Name prefix of the variables
        count : int
            Number of requested variables
        min_value : float
            Variables minimal value
        max_value : float
            Variables maximal value
        """
        return [self.get_new_discrete_variable(base_name+str(i), min_value, max_value) for i in range(count)]

    def sum_variables(self, array):
        """Returns the sum of MILP variables as accepted by the module.

        Parameters
        ----------
        array : list
            List of variables that have to be summed
        """
        return mip.xsum(array)

    def get_model(self):
        """Returns the MILP module python model object.
        """
        return self.__model

    def add_equality(self, left_term, right_term):
        """Adds an equality constraint to the model (left_term = right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the equality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the equality
        """
        if isinstance(left_term, np.float_):
            left_term = float(left_term)
        if isinstance(right_term, np.float_):
            right_term = float(right_term)
            
        self.__model += (left_term == right_term)

    def add_lower_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term < right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        if isinstance(left_term, np.float_):
            left_term = float(left_term)
        if isinstance(right_term, np.float_):
            right_term = float(right_term)

        self.__model += left_term <= right_term

    def add_greater_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term > right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        if isinstance(left_term, np.float_):
            left_term = float(left_term)
        if isinstance(right_term, np.float_):
            right_term = float(right_term)
            
        self.__model += left_term >= right_term

    def set_objective(self, objective):
        """Sets the objective of the model.

        Parameters
        ----------
        objective : variable, linear expression or number understood by the module
            Objective value
        """
        self.__model.objective = objective

    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        All variables, constraints and objective must be set before. No check is done in this function.

        Parameters
        ----------
        solve_parameters : dict, optional
            Lists the interface solve options
        """
        status = self.__model.optimize()
        if not status in (
                mip.OptimizationStatus.OPTIMAL,
                mip.OptimizationStatus.FEASIBLE,
            ):
            raise UnsolvableProblemException()

    def get_results_from_variables(self, variable_dict) -> pd.DataFrame:
        """Returns the solved values of the given variables.

        Parameters
        ----------
        variable_dict : dict
            Dictionnary containing the variables whose solution is requested. 
        """
        new_df = pd.DataFrame()

        for component in variable_dict:
            for variable in variable_dict[component]:
                new_df.loc[:, component+"_"+variable] = variable_dict[component][variable]

        for column in new_df:
            if isinstance(new_df[column][0], mip.entities.Var):
                new_df.loc[:, column] = new_df[column].apply(lambda y: y.x)

        return new_df