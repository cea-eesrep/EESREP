
from os import environ
from eesrep.eesrep_io import ComponentIO
import pytest

import pandas as pd

import eesrep
from eesrep.components.generic_component import GenericComponent
from eesrep.eesrep_enum import TimeSerieType
from eesrep.solver_interface.generic_interface import GenericInterface

if "EESREP_SOLVER" not in environ:
    solver_for_tests = "CBC"
else:
    solver_for_tests = environ["EESREP_SOLVER"]

if solver_for_tests == "CBC":
    interface_for_tests = "mip"
else:
    interface_for_tests = "docplex"

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_component_name():
    """
        Tests if the cluster starts the right amount of machines
    """
    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(2.)
        assert False, "add_component must only accept generic components"
    except TypeError:
        assert True
        
@pytest.mark.Unit
@pytest.mark.component
def test_missing_component_name():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.time_series = {}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity": False
                                        }
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component name attributenot defined"
    except AttributeError:
        assert True
        
@pytest.mark.Unit
@pytest.mark.component
def test_component_name_already_exists():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = {}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var": ComponentIO(self.name, "intensive_var", TimeSerieType.INTENSIVE, False)
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    model.add_component(FakeComponent("fake"))
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component name already defined"
    except ValueError:
        assert True

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_time_serie_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = ["element_1"]

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity": False
                                        }
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component time serie should be a dict"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_time_serie_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = ["element_1"]

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity": False
                                        }
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component time serie should be a dict"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_time_serie_element():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = {"var_1" : pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]})}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity": False
                                        }
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component time serie element should be a dict"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_time_serie_element_missing_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = {"var_1" : {
                    "value": pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]})
                }}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity": False
                                        }
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component time serie element should be a dict"
    except KeyError:
        assert True

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_time_serie_element_wrong_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = {"var_1" : {
                    "value": pd.DataFrame({"time":[0,1,2,3,4,5], "value":[0,1,2,3,4,5]}),
                    "type": True
                }}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity": False
                                        }
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component time serie element should be a dict"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_time_serie_element_wrong_value():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = {"var_1" : {
                    "value": [0,1,2,3,4,5],
                    "type": TimeSerieType.EXTENSIVE
                }}

        def io_from_parameters(self) -> dict:
            return { 
                        "intensive_var":{
                                            "type": TimeSerieType.INTENSIVE,
                                            "continuity": False
                                        }
                    }

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "Component time serie element should be a dict"
    except TypeError:
        assert True

@pytest.mark.Unit
@pytest.mark.component
def test_wrong_io_type():
    """
        Tests if the cluster starts the right amount of machines
    """
    class FakeComponent(GenericComponent):
        def __init__(self, name:str):
            self.name = name
            self.time_series = {}

        def io_from_parameters(self) -> dict:
            return  ["intensive_var"]

        def build_model(self,
            component_name:str,
            time_steps:list,
            time_series:pd.DataFrame,
            history:pd.DataFrame,
            model_interface:GenericInterface):
            
            variables = {}
            objective = 0.

            return variables, objective

    model = eesrep.Eesrep(solver=solver_for_tests, interface=interface_for_tests)
    
    try:
        model.add_component(FakeComponent("fake"))
        assert False, "io definition should be a dict"
    except TypeError:
        assert True