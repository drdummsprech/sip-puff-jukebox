from abc import ABC, abstractmethod


class IPressureSensor(ABC):
    """Interface for pressure sensors to be used for generating input"""

    @abstractmethod
    def get_pressure_in_Pascal(self) -> float:
        pass
