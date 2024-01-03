from typing import List

from eesrep.solver_interface.generic_interface import GenericInterface
from eesrep.eesrep_exceptions import *

class InterfaceTester:
    def __init__(self) -> None:
        self.interface_class:GenericInterface = None

    def test(self, interface_class:GenericInterface):
        self.interface_class = interface_class

        self.test_continuous_variable_list()
        self.test_discrete_variable_list()
        self.test_variable_none_bounds()
        self.test_variable_list_none_bounds()

        self.test_equality()
        self.test_sum()
        self.test_objective()
        self.test_greater_than()
        self.test_lower_than()

        self.test_unsolvable()
        self.test_discrete_vs_continuous()
    
    def test_continuous_variable_list(self):
         interface:GenericInterface = self.interface_class()

         type_variable = type(interface.get_new_continuous_variable("test", 0, 1))

         var_list = interface.get_new_continuous_variable_list("test", 10, 0, 1)

         assert isinstance(var_list, list), "Continuous list not working."
         assert len(var_list) == 10, "Continuous list not working."

         for elem in var_list:
            assert isinstance(elem, type_variable), "Continuous list not working."

    def test_discrete_variable_list(self):
         interface:GenericInterface = self.interface_class()

         type_variable = type(interface.get_new_discrete_variable("test", 0, 1))

         var_list = interface.get_new_discrete_variable_list("test", 10, 0, 1)

         assert isinstance(var_list, list), "Discrete list not working."
         assert len(var_list) == 10, "Discrete list not working."

         for elem in var_list:
            assert isinstance(elem, type_variable), "Discrete list not working."

    def test_variable_none_bounds(self):
         interface:GenericInterface = self.interface_class()

         type_variable = type(interface.get_new_continuous_variable("test", 0, 1))

         assert isinstance(interface.get_new_continuous_variable("test1", None, 1), type_variable), "None lower bound refused."
         assert isinstance(interface.get_new_continuous_variable("test2", 0, None), type_variable), "None higher bound refused."
         assert isinstance(interface.get_new_continuous_variable("test3", None, None), type_variable), "Both None bound refused."

         type_variable = type(interface.get_new_discrete_variable("test4", 0, 1))

         assert isinstance(interface.get_new_discrete_variable("test5", None, 1), type_variable), "None lower bound refused."
         assert isinstance(interface.get_new_discrete_variable("test6", 0, None), type_variable), "None higher bound refused."
         assert isinstance(interface.get_new_discrete_variable("test7", None, None), type_variable), "Both None bound refused."
         
    def test_variable_list_none_bounds(self):
         interface:GenericInterface = self.interface_class()

         type_variable = type(interface.get_new_continuous_variable("test1", 0, 1))

         assert isinstance(interface.get_new_continuous_variable_list("test2", 10, None, 1), List), "None lower bound refused."
         assert isinstance(interface.get_new_continuous_variable_list("test3", 10, 0, None), List), "None higher bound refused."
         assert isinstance(interface.get_new_continuous_variable_list("test4", 10, None, None), List), "Both None bound refused."
         
         assert all(isinstance(x, type_variable) for x in interface.get_new_continuous_variable_list("test2.2", 10, None, 1)), "None lower bound refused."
         assert all(isinstance(x, type_variable) for x in interface.get_new_continuous_variable_list("test3.2", 10, 0, None)), "None higher bound refused."
         assert all(isinstance(x, type_variable) for x in interface.get_new_continuous_variable_list("test4.", 10, None, None)), "Both None bound refused."

         type_variable = type(interface.get_new_discrete_variable("test5", 0, 1))

         assert isinstance(interface.get_new_discrete_variable_list("test6", 10, None, 1), List), "None lower bound refused."
         assert isinstance(interface.get_new_discrete_variable_list("test7", 10, 0, None), List), "None higher bound refused."
         assert isinstance(interface.get_new_discrete_variable_list("test8", 10, None, None), List), "Both None bound refused."

         assert all(isinstance(x, type_variable) for x in interface.get_new_discrete_variable_list("test6.2", 10, None, 1)), "None lower bound refused."
         assert all(isinstance(x, type_variable) for x in interface.get_new_discrete_variable_list("test7.2", 10, 0, None)), "None higher bound refused."
         assert all(isinstance(x, type_variable) for x in interface.get_new_discrete_variable_list("test8.2", 10, None, None)), "Both None bound refused."

    def test_equality(self):
        interface:GenericInterface = self.interface_class()

        var = interface.get_new_continuous_variable("test", 0, 1)

        interface.add_equality(var, 0.5)

        interface.solve()

        assert interface.get_results_from_variables({"component":{"test":[var]}}).values == [0.5], "Equality constraint not working"

    def test_sum(self):
        interface:GenericInterface = self.interface_class()

        var = interface.get_new_continuous_variable("test", 0, 1)
        var2 = interface.get_new_continuous_variable("test2", 0, 1)

        interface.add_equality(interface.sum_variables([var + var2]), 0.5)

        interface.solve()

        assert sum(interface.get_results_from_variables({"component":{"test":[var, var2]}}).values) == [0.5], "Sum not working"

    def test_objective(self):
        interface:GenericInterface = self.interface_class()

        var = interface.get_new_continuous_variable("test", 0, 1)
        var2 = interface.get_new_continuous_variable("test2", 0, 1)

        interface.add_equality(interface.sum_variables([var + var2]), 0.5)
        interface.set_objective(var)

        interface.solve()

        assert float(interface.get_results_from_variables({"component":{"test":[var]}}).values) == 0., "Objective constraint not working"
        assert float(interface.get_results_from_variables({"component":{"test":[var2]}}).values) == 0.5, "Objective constraint not working"
        

    def test_greater_than(self):
        interface:GenericInterface = self.interface_class()

        var = interface.get_new_continuous_variable("test", 0, 1)

        interface.add_greater_than(var, 0.5)
        interface.set_objective(var)

        interface.solve()

        assert float(interface.get_results_from_variables({"component":{"test":[var]}}).values) == 0.5, "Greater than constraint not working"
        
    def test_lower_than(self):
        interface:GenericInterface = self.interface_class()

        var = interface.get_new_continuous_variable("test", 0, 1)

        interface.add_lower_than(var, 0.5)
        interface.set_objective(-var)

        interface.solve()

        assert float(interface.get_results_from_variables({"component":{"test":[var]}}).values) == 0.5, "Lower than constraint not working"
        
    def test_unsolvable(self):
        interface:GenericInterface = self.interface_class()

        var = interface.get_new_continuous_variable("test", 0, 1)

        interface.add_equality(var, 5)

        try:
            interface.solve()
            assert False, "The problem is unsolvable."
        except UnsolvableProblemException:
            assert True

    def test_discrete_vs_continuous(self):
        interface:GenericInterface = self.interface_class()

        var = interface.get_new_continuous_variable("test", 0, 10)
        var2 = interface.get_new_discrete_variable("test2", 0, 10)

        interface.add_equality(interface.sum_variables([var + var2]), 5.1)
        interface.set_objective(var)

        interface.solve()

        assert abs(float(interface.get_results_from_variables({"component":{"test":[var]}}).values) - 0.1) < 1e-5, "Discrete-continuous variable types are wrong."
        assert abs(float(interface.get_results_from_variables({"component":{"test":[var2]}}).values) - 5.) < 1e-5, "Discrete-continuous variable types are wrong."