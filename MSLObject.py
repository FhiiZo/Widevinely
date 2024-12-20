import jsonpickle


class MSLObject:

    def __repr__(self) -> str:
        return "<{} {}>".format(self.__class__.__name__, jsonpickle.encode(self, unpicklable=False))
