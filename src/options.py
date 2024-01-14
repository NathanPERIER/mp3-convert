
from src.metadata.keep import ConvertKeep


class ProgramOptions :

    def __init__(self) :
        self.can_remove: bool           = True
        self.dry_run:    bool           = False
        self.default_keep:  ConvertKeep = ConvertKeep.ALWAYS
        self.keep_treshold: ConvertKeep = ConvertKeep.lowest()


options = ProgramOptions()
