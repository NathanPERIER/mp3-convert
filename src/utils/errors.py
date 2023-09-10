
class UnreachableCode(Exception):

    def __init__(self):
        super().__init__('Executed theorically unreachable code')

