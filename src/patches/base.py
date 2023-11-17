
from abc import ABC, abstractmethod


class Patch(ABC) :

    @abstractmethod
    def apply(self) :
        pass

    @abstractmethod
    def describe(self) -> str :
        pass
