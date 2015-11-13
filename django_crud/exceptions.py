

class CrudError(Exception):
    pass


class AttrCrudError(AttributeError, CrudError):
    pass


class SetupCrudError(AssertionError, CrudError):
    pass
