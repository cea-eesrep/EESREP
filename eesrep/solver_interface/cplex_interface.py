"""Module providing an interface between Eersep and the docplex module."""

from typing import List, Tuple

import cplex
import pandas as pd

from eesrep.eesrep_exceptions import *
from eesrep.solver_interface.generic_interface import GenericInterface


class CplexElement():
    """This class defines an object that is used to store the equations for the EESREP cplex interface."""
    def __init__(self, value:List[Tuple[str, float]]):
        """Initialises a CplexElement using a tuple of string (variable name) and float (coefficient in the equation).

        Parameters
        ----------
        value : List[Tuple[str, float]]
            Equation description
        """        
        self.array = value

    def __mul__(self, other):
        """Definition of the CplexElement multiplication

        Parameters
        ----------
        other
            Object to which the element is multiplied

        Returns
        -------
        CplexElement
            Output equation
        """        
        if isinstance(other, float) or isinstance(other, int):
            return CplexElement([(elem[0], other*elem[1]) for elem in self.array])
        else:
            out_dict = {}
            for elem in self.array:
                if elem[0] in other:
                    out_dict[elem[0]] = elem[1] * other[elem[0]]

            return CplexElement([(key, val) for key, val in zip(list(out_dict.keys()), list(out_dict.values()))])

    def __rmul__(self, other):
        """Definition of the CplexElement multiplication

        Parameters
        ----------
        other
            Object to which the element is multiplied

        Returns
        -------
        CplexElement
            Output equation
        """        
        return self.__mul__(other)

    def __floordiv__(self, other):
        """Definition of the CplexElement division

        Parameters
        ----------
        other
            Object by which the element is divided

        Returns
        -------
        CplexElement
            Output equation

        Raises
        ------
        TypeError
            Cant divide by a CplexElement
        """        
        if isinstance(other, float) or isinstance(other, int):
            return CplexElement([(elem[0], elem[1]/other) for elem in self.array])
        else:
            raise TypeError("Cant divide by a CplexElement")

    def __truediv__(self, other):
        """Definition of the CplexElement division

        Parameters
        ----------
        other
            Object by which the element is divided

        Returns
        -------
        CplexElement
            Output equation
        """        
        return self.__floordiv__(other)

    def __add__(self, other):
        """Definition of the CplexElement addition

        Parameters
        ----------
        other
            Object to which the element is added

        Returns
        -------
        CplexElement
            Output equation
        """        
        if isinstance(other, float) or isinstance(other, int):
            new_array = self.array.copy()
            if 1 in [elem[0] for elem in self.array]:
                index = [elem[0] for elem in self.array].index(1)
                new_array[index] = (new_array[index][0], new_array[index][1]+other)
            else:
                new_array.append([1, other])

            return CplexElement(new_array) #CplexElement([(elem[0], other+elem[1]) for elem in self.array])
        else:
            out_dict = {elem[0]:elem[1] for elem in self.array}
            
            for elem in other:
                if elem[0] in out_dict:
                    out_dict[elem[0]] += elem[1]
                else:
                    out_dict[elem[0]] = elem[1]

            return CplexElement([(key, val) for key, val in zip(list(out_dict.keys()), list(out_dict.values()))])

    def __radd__(self, other):
        """Definition of the CplexElement addition

        Parameters
        ----------
        other
            Object to which the element is added

        Returns
        -------
        CplexElement
            Output equation
        """        
        return self.__add__(other)

    #   self - other
    def __sub__(self, other):
        """Definition of the CplexElement substraction

        Parameters
        ----------
        other
            Object subtracted to self

        Returns
        -------
        CplexElement
            Output equation
        """        
        return self.__add__(-other)

    #   other - self
    def __rsub__(self, other):
        """Definition of the CplexElement substraction

        Parameters
        ----------
        other
            Object from which self is subtracted

        Returns
        -------
        CplexElement
            Output equation
        """        
        return other.__sub__(self)
        
    def __neg__(self):
        """Definition of the CplexElement negation

        Returns
        -------
        CplexElement
            The opposite of self
        """        
        new_array = self.array.copy()
        for i in range(len(self.array)):
            new_array[i] = (self.array[i][0], -self.array[i][1])
        return CplexElement(new_array)
        
    def __getitem__(self, item):
        return self.array[item]

    def __repr__(self):
        return f'<CplexElement({self.array})>'

    def copy(self):
        """Returns a copy of self

        Returns
        -------
        CplexElement
            A copy of self
        """        
        return CplexElement(self.array)

class CplexInterface(GenericInterface):
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
        self.direction = direction
        self.__model = cplex.Cplex()

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
        if min_value == None:
            min_value = -cplex.infinity
        if max_value == None:
            max_value = cplex.infinity
        self.__model.variables.add(names = [name], lb = [min_value], ub = [max_value])
        return CplexElement([(name, 1.)])

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
        if min_value == None:
            min_value = -cplex.infinity
        if max_value == None:
            max_value = cplex.infinity
        self.__model.variables.add(names = [name], lb = [min_value], ub = [max_value], types = [self.__model.variables.type.integer])
        return CplexElement([(name, 1.)])

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
        if min_value == None:
            min_value = -cplex.infinity
        if max_value == None:
            max_value = cplex.infinity

        self.__model.variables.add(names = [base_name+f"_{i}" for i in range(count)], 
                                            lb = [min_value]*count, 
                                            ub = [max_value]*count)
        return [CplexElement([(base_name+f"_{i}", 1.)]) for i in range(count)]

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
        if min_value == None:
            min_value = -cplex.infinity
        if max_value == None:
            max_value = cplex.infinity
        self.__model.variables.add(names = [base_name+f"_{i}" for i in range(count)], 
                                            lb = [min_value]*count, 
                                            ub = [max_value]*count, 
                                            types = [self.__model.variables.type.integer]*count)
        return [CplexElement([(base_name+f"_{i}", 1.)]) for i in range(count)]

    def sum_variables(self, array:List):
        """Returns the sum of MILP variables as accepted by the module.

        Parameters
        ----------
        array : list
            List of variables that have to be summed
        """
        if len(array) == 0:
            return 0.
        
        out_dict = {}
        
        for elem_array in array:
            if isinstance(elem_array, CplexElement):
                for elem in elem_array:
                    if not elem[0] in out_dict:
                        out_dict[elem[0]] = elem[1]
                    else:
                        out_dict[elem[0]] += elem[1]
            else:
                if 1 in out_dict:
                    out_dict[1] += elem_array
                else:
                    out_dict[1] = elem_array

        return CplexElement([(key, val) for key, val in zip(list(out_dict.keys()), list(out_dict.values()))])

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

        if not (isinstance(left_term, CplexElement) or isinstance(right_term, CplexElement)):
            raise TypeError("Left or right term should be a CplexElement.")

        new_left_term:CplexElement = self.sum_variables([left_term, -right_term])

        right_term = 0

        if 1 in [elem[0] for elem in new_left_term.array]:
            index = [elem[0] for elem in new_left_term.array].index(1)
            right_term -= new_left_term.array[index][1]
            del new_left_term.array[index]

        self.__model.linear_constraints.add(
                                                lin_expr=[cplex.SparsePair(ind = [elem[0] for elem in new_left_term], val = [elem[1] for elem in new_left_term])],
                                                senses=["E"],
                                                rhs=[right_term]
                                            )

    def add_lower_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term < right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        if not (isinstance(left_term, CplexElement) or isinstance(right_term, CplexElement)):
            raise TypeError("Left or right term should be a CplexElement.")

        new_left_term:CplexElement = left_term - right_term

        right_term = 0

        if 1 in [elem[0] for elem in new_left_term.array]:
            index = [elem[0] for elem in new_left_term.array].index(1)
            right_term -= new_left_term.array[index][1]
            del new_left_term.array[index]

        self.__model.linear_constraints.add(
                                                lin_expr=[cplex.SparsePair(ind = [elem[0] for elem in new_left_term], val = [elem[1] for elem in new_left_term])],
                                                senses=["L"],
                                                rhs=[right_term]
                                            )

    def add_greater_than(self, left_term, right_term):
        """Adds an inequality constraint to the model (left_term > right_term).

        Parameters
        ----------
        left_term : variable, linear expression or number understood by the module
            Left hand side of the inequality
        right_term : variable, linear expression or number understood by the module
            Right hand side of the inequality
        """
        if not (isinstance(left_term, CplexElement) or isinstance(right_term, CplexElement)):
            raise TypeError("Left or right term should be a CplexElement.")

        new_left_term:CplexElement = left_term - right_term

        right_term = 0

        if 1 in [elem[0] for elem in new_left_term.array]:
            index = [elem[0] for elem in new_left_term.array].index(1)
            right_term -= new_left_term.array[index][1]
            del new_left_term.array[index]

        self.__model.linear_constraints.add(
                                                lin_expr=[cplex.SparsePair(ind = [elem[0] for elem in new_left_term], val = [elem[1] for elem in new_left_term])],
                                                senses=["G"],
                                                rhs=[right_term]
                                            )

    def set_objective(self, objective):
        """Sets the objective of the model.

        Parameters
        ----------
        objective : variable, linear expression or number understood by the module
            Objective value
        """
        if isinstance(objective, CplexElement):
            if 1 in [elem[0] for elem in objective.array]:
                index = [elem[0] for elem in objective.array].index(1)
                del objective.array[index]
            self.__model.objective.set_linear(objective.array)


    def solve(self, solve_parameters:dict = {}):
        """Solves the created model.

        All variables, constraints and objective must be set before. No check is done in this function.

        Parameters
        ----------
        solve_parameters : dict, optional
            Lists the interface solve options:
            - write_problem : Writes the problem in a .lp file
        """
        
        if self.direction.lower() == "minimize":
            self.__model.objective.set_sense(self.__model.objective.sense.minimize)
        else:
            self.__model.objective.set_sense(self.__model.objective.sense.maximize)

        if self.__model.variables.get_num_binary() + self.__model.variables.get_num_integer() > 0:
            self.__model.set_problem_type(self.__model.problem_type.MILP)
        else:
            self.__model.set_problem_type(self.__model.problem_type.LP)
        
        if "write_problem" in solve_parameters and solve_parameters["write_problem"]:
            self.__model.write("problem.lp")

        self.__model.solve()
        
        if self.__model.solution.get_status() == 0:
            raise UnsolvableProblemException()

    def query_solution(self, elem:CplexElement, solution:dict):
        return solution[elem.array[0][0]]

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

        solution = dict(zip(self.__model.variables.get_names(),self.__model.solution.get_values()))

        for column in new_df:
            if type(new_df[column][0]) in [CplexElement]:
                new_df.loc[:, column] = new_df[column].apply(lambda x:self.query_solution(x, solution))

        return new_df
