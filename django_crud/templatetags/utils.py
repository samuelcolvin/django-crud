from django.utils.html import escape
from django.utils.safestring import SafeData, mark_safe
from jinja2 import Undefined
from django_jinja import library


@library.test(name='iterable')
def is_iterable(obj):
    """
    Test if an object is defined iterable. Usage {% if foo is iterable %}

    This is similar to {% if foo %} except empty lists evaluate to True.
    """
    if isinstance(obj, Undefined):
        return False
    return hasattr(obj, '__iter__')


@library.filter
def paragraphs(text):
    """
    Add line breaks to text to implement line breaks
    """
    if isinstance(text, SafeData):
        return text
    text = escape(text)
    return mark_safe('<p class="no-margin">{}</p>'.format(text.replace('\n', '</p>\n<p class="no-margin">')))
