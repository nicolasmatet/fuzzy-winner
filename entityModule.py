def get_entity_dict(entity_id, exogen_revenue):
    return {"id":entity_id, "exogen_revenue":exogen_revenue}

class Entity:
    def __init__(self, **kargs):
        self.__dict__.update(**kargs)

    def get_id(self):
        return self.__dict__.get("id", -1)

    def __key(self):
        return (self.get_id())

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())