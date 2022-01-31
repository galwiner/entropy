from abc import ABC
from qualang_tools.config import ConfigBuilder as cb




class QCONTROLLERS(Enum):
    OPX = auto()
    OPXPlus = auto()
    OPY = auto()
    OPZ = auto()

# class Quam:

#     def __init__(self,path='.') -> None:
#         super().__init__()
#         self._resources = LabResources(db=path)


# def quam_init(path='.',name = None):
#     # this function initializes the quam system (it will be part of the quam)

#     quam = Quam(path,name)
#     admin = QuamAdmin(path,name)
#     oracle = QuamOracle(path,name)
#     return quam, admin, oracle

# def create_quam(name,path,**kwargs):
#     #mk param store
#     #mk resources DB, or add to exisiting and save quam under the provided name
#     #check if name exists in current project, and if so return exception.
#     pass
class ParamStore:
    def __init__(self) -> None:
        pass
class ParamStoreConnector:
    @staticmethod
    def connect(path) -> ParamStore:
        pass

#this class represents an entity that can control  instruments
class Element(ABC):
    def __init__(self,path='.entropy') -> None:
        self.params = []
        self.instruments =[]


#this class represents an entity that has both a QUA controller and other instruments
#in other words: a QUA element has a ConfigBuilder object 
class QuaElement(Element,ABC):

    def __init__(self, path='.entropy') -> None:
        super().__init__(path)
        self.configBuilder = cb.ConfigBuilder()

class QuamAdmin():
    def __init__(self,path='.entropy') -> None:
        self.paramStore = ParamStoreConnector.connect(paramStore_path=path)
        elements = []

    def add(self, element: Element):
        self.element.append(element)


