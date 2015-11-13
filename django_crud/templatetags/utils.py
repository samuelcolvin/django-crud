from django_jinja import library
from jinja2 import Undefined


@library.test(name='iterable')
def is_iterable(obj):
    """
    Test if an object is defined iterable. Usage {% if foo is iterable %}

    This is similar to {% if foo %} except empty lists evaluate to True.
    """
    if isinstance(obj, Undefined):
        return False
    return hasattr(obj, '__iter__')
