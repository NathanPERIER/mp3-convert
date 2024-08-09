
from enum import Enum

from typing import Optional


class ConvertKeep(Enum) :
    ALWAYS = 1
    BONUS = 2
    ARCHIVE = 3
    SKIP = 4

    def parse(repr: str) -> "Optional[ConvertKeep]" :
        names_mapping = {
            'always': ConvertKeep.ALWAYS,
            'keep': ConvertKeep.ALWAYS,
            'bonus': ConvertKeep.BONUS,
            'archive': ConvertKeep.ARCHIVE,
            'never': ConvertKeep.SKIP,
            'skip': ConvertKeep.SKIP,
        }
        return names_mapping.get(repr.lower())

    def lowest() -> "ConvertKeep" :
        return ConvertKeep.SKIP

    def __le__(self, other: "ConvertKeep") -> bool :
        return self.value <= other.value
