
from abc import ABC, abstractmethod


class Patch(ABC) :

    @abstractmethod
    def apply(self) :
        pass

    @abstractmethod
    def get_name(self) -> str :
        pass

    @abstractmethod
    def describe(self) -> str :
        pass
