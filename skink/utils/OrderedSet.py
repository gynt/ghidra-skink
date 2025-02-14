from typing import Iterable

def uniques(iterable):
    lst = []
    for i in iterable:
        if not i in lst:
            lst.append(i)
            yield i

class OrderedSet[T](list):

    def __init__(self, iterable: Iterable[T]):
        super().__init__(uniques(iterable))

    def add(self, value: T):
        if not value in self:
            super().append(value)

    def __add__(self, lst: Iterable[T]):
        nl = OrderedSet(self)
        for v in lst:
            nl.add(v)
        return nl

    def __iadd__(self, lst: Iterable[T]):
        for v in lst:
            self.add(v)
        return self

    def append(self, value: T):
        self.add(value)
    