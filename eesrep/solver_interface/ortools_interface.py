"""Module providing an interface between Eersep and the docplex module."""

import pandas as pd
from ortools.linear_solver import pywraplp
from ortools.linear_solver.python.linear_solver_natural_api import SumArray

from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_exceptions import *

class OrtoolsInterface(GenericInterface):
    """Interface class between the python ORTOOLS module and Esreep."""
    def __init__(self, direction = "minimize", solver = "GLOP"):
        """Initialises the inteface object, and stores the direction and solver for later use.

        Parameters
        ----------
        direction : str, optional
            Direction in which the objective must be optimised, can be Minimize or Maximize, by default "Minimize"
        solver : str, optional
            Solver used by the module, by default "CPLEX" if available
        """
        if direction.lower() == "minimize":
            self.__direction = "min"
        else:
            self.__direction = "max"

        self.__model = pywraplp.Solver.CreateSolver(solver)

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
        if min_value is None:
            min_value = -self.__model.infinity()

        if max_value is None:
            max_value = self.__model.infinity()

        return self.__model.NumVar(min_value, max_value, name)

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
        if min_value is None:
            min_value = -self.__model.infinity()

        if max_value is None:
            max_value = self.__model.infinity()

        return self.__model.IntVar(min_value, max_value, name)

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
        if isinstance(array, SumArray):
            return array
        return self.__model.Sum(array)

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
        self.__model.Add(left_term == right_term)

    def add_lower_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term < right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        self.__model.Add(left_term <= right_term)

    def add_greater_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term > right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        self.__model.Add(left_term >= right_term)

    def set_objective(self, objective):
        """Sets the objective of the model.

        Parameters
        ----------
        objective : variable, linear expression or number understood by the module
            Objective value
        """
        if self.__direction == "min":
            self.__model.Minimize(objective)
        else:
            self.__model.Maximize(objective)


    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        All variables, constraints and objective must be set before. No check is done in this function.

        Parameters
        ----------
        solve_parameters : dict, optional
            Lists the interface solve options:
            Writes or prints the log of the resolution, by default False
        """

        gap = float(solve_parameters["gap"]) if "gap" in solve_parameters else 0.
        solverParams = pywraplp.MPSolverParameters()
        solverParams.SetDoubleParam(solverParams.RELATIVE_MIP_GAP, gap)

        if "write_problem" in solve_parameters and solve_parameters["write_problem"]:
            with open("model.lp", 'w+') as f:
                f.write(self.__model.ExportModelAsLpFormat(False))

        self.solve_status = self.__model.Solve(solverParams)


        if not (self.solve_status == self.__model.OPTIMAL or self.solve_status == self.__model.FEASIBLE):
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
            if type(new_df[column][0]) in [pywraplp.Variable, pywraplp.VariableExpr]:
                new_df.loc[:, column] = new_df[column].apply(lambda x:x.solution_value())

        return new_df


    def get_result_objective(self) -> float:
        """Returns the objective value of the solution.

        Returns
        -------
        float
            Solution objective value

        Raises
        ------
        UnsolvedProblemException
            The problem was not solved yet
        """        
        if self.solve_status is None:
            raise UnsolvedProblemException

        return self.__model.Objective().Value()

