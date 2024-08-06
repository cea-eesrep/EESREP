"""Module providing an interface between Eersep and the docplex module."""

from docplex.mp.linear import Var, LinearExpr
from docplex.mp.model import Model
import pandas as pd

from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_exceptions import SolverOptionException, UnsolvableProblemException, UnsolvedProblemException
from eesrep.eesrep_enum import SolverOption

class DocplexInterface(GenericInterface):
    """Interface class between the python DOCPLEX module and Esreep."""
    def __init__(self, direction = "minimize", solver = "CPLEX"):
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

        self.__model:Model = Model()
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
        return self.__model.continuous_var(name=name, lb=min_value, ub= max_value)

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
        return self.__model.integer_var(name=name, lb=min_value, ub= max_value)

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
        return self.__model.continuous_var_list(count, lb=min_value, ub=max_value, name=base_name)

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
        return self.__model.integer_var_list(count, lb=min_value, ub=max_value, name=base_name)

    def sum_variables(self, array):
        """Returns the sum of MILP variables as accepted by the module.

        Parameters
        ----------
        array : list
            List of variables that have to be summed
        """
        return self.__model.sum(array)

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
        self.__model += left_term == right_term

    def add_lower_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term < right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
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
        self.__model += left_term >= right_term

    def set_objective(self, objective):
        """Sets the objective of the model.

        Parameters
        ----------
        objective : variable, linear expression or number understood by the module
            Objective value
        """
        self.__model.set_objective(self.__direction, objective)

    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        All variables, constraints and objective must be set before. No check is done in this function.

        Parameters
        ----------
        solve_parameters : dict, optional
            Lists the interface solve options:
            Writes or prints the log of the resolution, by default False
            
        Raises
        ------
            SolverOptionException
                One of the solve parameters is not implemented for this interface.
        """

        #   Parameters help : https://www.ibm.com/docs/en/icos/12.9.0?topic=cplex-list-parameters
        
        mipgap = 0
        threads = 8
        method = "concurrent"
        start_algorithm = "concurrent"
        write_lp = False
        print_log = False
        dual_prepro = False

        for option in solve_parameters:
            if option == SolverOption.MILP_GAP:
                mipgap = float(solve_parameters[SolverOption.MILP_GAP])
                
            elif option == SolverOption.THREADS:
                threads = int(solve_parameters[SolverOption.THREADS])

            elif option == SolverOption.METHOD:
                method = solve_parameters[SolverOption.METHOD]
            
            elif option == SolverOption.TIME_LIMIT:
                self.__model.parameters.timelimit = float(solve_parameters[SolverOption.TIME_LIMIT])
            
            elif option == SolverOption.WRITE_PROBLEM:
                write_lp = solve_parameters[SolverOption.WRITE_PROBLEM]
            
            elif option == SolverOption.PRINT_LOG:
                print_log = solve_parameters[SolverOption.PRINT_LOG]

            elif option == "start_algorithm":
                start_algorithm = solve_parameters["start_algorithm"]

            elif option == "dual_prepro":
                dual_prepro = solve_parameters["dual_prepro"]
            
            else:
                raise SolverOptionException(option, self.__class__.__name__)

        self.__model.parameters.mip.tolerances.mipgap = mipgap
        self.__model.parameters.threads = threads

        if method == "automatic":
            self.__model.parameters.lpmethod = 0
        elif method == "primal_simplex":
            self.__model.parameters.lpmethod = 1
        elif method == "dual_simplex":
            self.__model.parameters.lpmethod = 2
        elif method == "barrier":
            self.__model.parameters.lpmethod = 4
        elif method == "concurrent":
            self.__model.parameters.lpmethod = 6
        
        if dual_prepro:
            self.__model.parameters.preprocessing.dual = 1

        # https://www.ibm.com/docs/en/icos/22.1.0?topic=parameters-algorithm-initial-mip-relaxation
        # parameters.mip.strategy.startalgorithm
        
        if start_algorithm == "automatic":
            self.__model.parameters.mip.strategy.startalgorithm = 0
        elif start_algorithm == "primal_simplex":
            self.__model.parameters.mip.strategy.startalgorithm = 1
        elif start_algorithm == "dual_simplex":
            self.__model.parameters.mip.strategy.startalgorithm = 2
        elif start_algorithm == "barrier":
            self.__model.parameters.mip.strategy.startalgorithm = 4
        elif start_algorithm == "concurrent":
            self.__model.parameters.mip.strategy.startalgorithm = 6

        if write_lp:
            self.__model.export_as_lp("my_problem.lp")

        self.solve_status = self.__model.solve(log_output = print_log)

        if self.solve_status is None:
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
            if type(new_df[column][0]) in [Var, LinearExpr]:
                new_df.loc[:, column] = new_df[column].apply(lambda x:x.solution_value)

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

        return self.__model.multi_objective_values[0]

