
from enum import Enum


class ConvertKeep(Enum) :
    ALWAYS = 1
    BONUS = 2
    SKIP = 3

    def lowest() -> "ConvertKeep" :
        return ConvertKeep.SKIP

    def __le__(self, other: "ConvertKeep") -> bool :
        return self.value <= other.value
