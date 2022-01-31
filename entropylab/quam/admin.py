from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from qualang_tools.config import ConfigBuilder as cb
from qualang_tools.config import components as qua_components 
from tomlkit import value
from entropylab.quam.param_store import InProcessParamStore
from qualang_tools.config.parameters import ConfigVar
from entropylab.quam.utils import DotDict






class QCONTROLLERS(Enum):
    OPX = auto()
    OPXPlus = auto()
    OPY = auto()
    OPZ = auto()

# class Quam:

#     def __init__(self,path='.') -> None:
#         super().__init__()
#         self._resources = LabResources(db=path)


def quam_init(path='.',name = None):
    # this function initializes the quam system (it will be part of the quam)

    # quam = Quam(path,name)
    quam =None
    admin = QuamAdmin(path,name)
    # oracle = QuamOracle(path,name)
    oracle =None
    return admin, quam, oracle

# def create_quam(name,path,**kwargs):
#     #mk param store
#     #mk resources DB, or add to exisiting and save quam under the provided name
#     #check if name exists in current project, and if so return exception.
#     pass
class ParamStoreConnector:
    @staticmethod
    def connect(path) -> InProcessParamStore:
        return InProcessParamStore(path)
@dataclass
class UserParameter:

    key: str
    value 

# p = UserParameter('this','that')

# ParamStore['this'] = 'that'



# cup_of_water = Element()

# cup_of_water.add(Heater)
# cup_of_water.add(TempProbe)



#this class represents an entity that can control  instruments    
class Element(ABC):
    def __init__(self,name:str) -> None:
        self.name=name
        self.params = DotDict()
        self.instruments = DotDict()



#this class represents an entity that has both a QUA controller and other instruments
#in other words: a QUA element has a ConfigBuilder object 
class QuaElement(Element,ABC):

    def __init__(self, name:str) -> None:
        super().__init__(name)
    
    @abstractmethod
    def make_qua_component(self):
        pass
class Transmon(QuaElement):
    def __init__(self, name:str, *args) -> None:
        self.args = args 
        super().__init__(name)
        
    def make_qua_component(self):        
        return qua_components.Transmon(*self.args)

class FluxTunableTransmon(QuaElement):
    def __init__(self, name:str, *args) -> None:
        self.args = args 
        super().__init__(name)
    
    def make_qua_component(self):        
        return qua_components.FluxTunableTransmon(*self.args)


class QuamAdmin():
    def __init__(self,name:str = None,path='.entropy/paramStore.db') -> None:
        self._paramStore = ParamStoreConnector.connect(path)
        self._configVar = ConfigVar()
        self.elements = DotDict()
        self.name=name

    def add(self, name:str, element: Element):
        self.elements[name]=element
    
    def add_parameter(self, name:str, val:Any,persistent = True):
        if persistent:
            self._paramStore._params[name] = val
        self._configVar.set(name=val)

    def commit(self,label:str=None):
        self._paramStore.commit(label)


