from django.core.urlresolvers import NoReverseMatch


class CrudError(Exception):
    pass


class AttrCrudError(AttributeError, CrudError):
    pass


class SetupCrudError(AssertionError, CrudError):
    pass


class ReverseCrudError(NoReverseMatch, CrudError):
    pass
