
default_print = lambda x: print(str(x))


class PrintIterator :

    def __init__(self, it, print_func = default_print) :
        self._wrapped = it
        self._print = print_func

    def __iter__(self) :
        return self

    def __next__(self) :
        res = next(self._wrapped)
        self._print(res)
        return res
