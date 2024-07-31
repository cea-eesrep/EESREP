"""Module providing an interface between Eersep and the docplex module."""

import pandas as pd

from eesrep.solver_options import SolverOption
from pyomo.opt import SolverFactory
import pyomo.environ as pyo
from pyomo.environ import value
from pyomo.core.base.var import ScalarVar
from pyomo.core.expr.numeric_expr import LinearExpression
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.util.infeasible import log_infeasible_constraints

from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_exceptions import *

class PyomoInterface(GenericInterface):
    """Interface class between the python PYOMO module and Esreep."""
    def __init__(self, direction = "minimize", solver = "CPLEX"):
        """Initialises the inteface object, and stores the direction and solver for later use.
        
        Parameters
        ----------
        direction : str, optional
            Direction in which the objective must be optimised, can be Minimize or Maximize, by default "Minimize"
        solver : str, optional
            Solver used by the module, by default "CPLEX" if available
        """

        if not solver.lower() in pyo.SolverFactory.__dict__['_cls'].keys():
            raise ValueError(f"Given solver {solver} is not available for pyomo module.")

        if "min" in direction.lower():
            self.__direction = pyo.minimize
        else:
            self.__direction = pyo.maximize

        self.__opt = SolverFactory(solver)
        self.__model = pyo.ConcreteModel()
        self.__model.constraints = pyo.ConstraintList()

        self.solve_status = None

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
        self.__model.__dict__[name] = pyo.Var(name=name, bounds=(min_value, max_value))
        self.__model.__dict__[name].construct()

        return self.__model.__dict__[name]

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
        self.__model.__dict__[name] = pyo.Var(name=name, bounds=(min_value, max_value), domain=pyo.Integers)
        self.__model.__dict__[name].construct()

        return self.__model.__dict__[name]

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
        var_arr = [self.get_new_continuous_variable(base_name+str(i), min_value, max_value) for i in range(count)]

        for i in range(count):
            name = base_name+str(i)
            self.__model.__dict__[name] = var_arr[i]

        return var_arr

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
        var_arr = [self.get_new_discrete_variable(base_name+str(i), min_value, max_value) for i in range(count)]

        for i in range(count):
            name = base_name+str(i)
            self.__model.__dict__[name] = var_arr[i]

        return var_arr

    def sum_variables(self, array):
        """Returns the sum of MILP variables as accepted by the module.

        Parameters
        ----------
        array : list
            List of variables that have to be summed
        """
        return pyo.quicksum(array)

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
        self.__model.constraints.add(left_term == right_term)

    def add_lower_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term < right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        self.__model.constraints.add(left_term <= right_term)

    def add_greater_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term > right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        self.__model.constraints.add(left_term >= right_term)

    def set_objective(self, objective):
        """Sets the objective of the model.

        Parameters
        ----------
        objective : variable, linear expression or number understood by the module
            Objective value
        """
        self.__model.objective = pyo.Objective(expr=objective, sense=self.__direction)

    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        All variables, constraints and objective must be set before. No check is done in this function.

        Parameters
        ----------
        solve_parameters : dict, optional
            Lists the interface solve options:
            - write_problem : Writes the problem in a .lp file
            
        Raises
        ------
            SolverOptionException
                One of the solve parameters is not implemented for this interface.
        """
        threads = 8
        write_lp = False
        print_log = False

        for option in solve_parameters:
            if option == SolverOption.THREADS:
                threads = int(solve_parameters[SolverOption.THREADS])

            elif option == SolverOption.WRITE_PROBLEM:
                write_lp = solve_parameters[SolverOption.WRITE_PROBLEM]
            
            elif option == SolverOption.PRINT_LOG:
                print_log = solve_parameters[SolverOption.PRINT_LOG]
            
            else:
                raise SolverOptionException(option, self.__class__.__name__)
            
        if write_lp:
            self.__model.write("my_problem.lp")
        
        self.__results = self.__opt.solve(self.__model, options={"threads": threads}, tee = print_log)

        if (self.__results.solver.status == SolverStatus.ok) and (self.__results.solver.termination_condition == TerminationCondition.optimal):
            self.solve_status = self.__results.solver.status
            pass
        elif (self.__results.solver.termination_condition == TerminationCondition.infeasible):
            import logging
            logging.INFO = 2000000000000
            log_infeasible_constraints(self.__model, log_expression=True, log_variables=True)

            raise UnsolvableProblemException()
        else:
            raise ValueError(f"Solver Status: {self.__results.solver.status}")

    def get_result(self, x):
        if isinstance(x, LinearExpression):
            x_coefs = x.linear_coefs
            x_vars = x.linear_vars

            return sum([x_coefs[i]*pyo.value(x_vars[i]) for i in range(len(x_coefs))])
        else:
            return pyo.value(x)

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
                new_df.loc[:, component+"_"+variable] = variable_dict[component][variable].copy()

        for column in new_df:
            if type(new_df[column][0]) in [ScalarVar]:
                new_df.loc[:, column] = new_df[column].apply(lambda x:self.get_result(x))

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

        return value(self.__model.objective)

