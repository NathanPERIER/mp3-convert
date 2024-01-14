
from enum import Enum


class ConvertKeep(Enum) :
    ALWAYS = 1
    BONUS = 2
    DROP = 3

    def lowest() -> "ConvertKeep" :
        return ConvertKeep.DROP

    def __gt__(self, other: "ConvertKeep") -> bool :
        return self.value > other.value
