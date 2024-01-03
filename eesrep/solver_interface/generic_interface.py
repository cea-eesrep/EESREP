"""Module providing a generic interface between Eersep and a solver."""
from abc import abstractmethod, ABC
import pandas as pd

class GenericInterface(ABC):
    """Generic interface between Eersep and a solver. Class to overwrite."""

    @abstractmethod
    def __init__(self, direction:str = "Minimize", solver:str = "CPLEX"):
        """Initialises the inteface object, and stores the direction and solver for later use
        
        Parameters
        ----------
        direction : str, optional
            Direction in which the objective must be optimised, can be Minimize or Maximize, by default "Minimize"
        solver : str, optional
            Solver used by the module, by default "CPLEX" if available

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
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

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
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

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
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

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
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

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def sum_variables(self, array:list):
        """Returns the sum of MILP variables as accepted by the module.

        Parameters
        ----------
        array : list
            List of variables that have to be summed

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def get_model(self):
        """Returns the MILP module python model object.

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def add_equality(self, left_term, right_term):
        """Adds an equality constraint to the model (left_term = right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the equality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the equality

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def add_lower_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term < right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def add_greater_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term > right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def set_objective(self, objective):
        """Sets the objective of the model.

        Parameters
        ----------
        objective : variable, linear expression or number understood by the module
            Objective value

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        All variables, constraints and objective must be set before. No check is done in this function.

        Parameters
        ----------
        solve_parameters : dict, optional
            Lists the interface solve options

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError

    @abstractmethod
    def get_results_from_variables(self, variable_dict:dict) -> pd.DataFrame:
        """Returns the solved values of the given variables.

        Parameters
        ----------
        variable_dict : dict
            Dictionnary containing the variables whose solution is requested. 

        Raises
        ------
        NotImplementedError
            Must be overridden by the solver interface
        """
        raise NotImplementedError
