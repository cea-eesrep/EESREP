"""Class defining the solver-interface key couple for unit and theory tests"""

from os import environ

def get_couple_from_key():
    if "EESREP_INTERFACE" not in environ:
        interface_for_tests = "mip"
    else:
        interface_for_tests = environ["EESREP_INTERFACE"].lower()

    if interface_for_tests == "mip":
        solver_for_tests = "cbc"
    elif interface_for_tests == "docplex":
        solver_for_tests = "cplex"
    elif interface_for_tests == "pyomo":
        solver_for_tests = "cplex"
    elif interface_for_tests == "ortools":
        solver_for_tests = "glop"
    else:
        raise ValueError(f"Interface {interface_for_tests} not valid for tests.")

    return solver_for_tests.upper(), interface_for_tests.upper()