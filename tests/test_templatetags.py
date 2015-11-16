import pytest
from django.utils.safestring import mark_safe
from jinja2 import Undefined
from django_crud.templatetags.utils import is_iterable, paragraphs


@pytest.mark.parametrize('input,expected', [
    ([1, 2, 3], True),
    (True, False),
    (False, False),
    (Undefined(), False),
    ('123', True),
])
def test_is_iterable(input, expected):
    assert is_iterable(input) == expected


@pytest.mark.parametrize('input,expected', [
    ('a single sentence', '<p class="no-margin">a single sentence</p>'),
    ('two sentences\nare here', '<p class="no-margin">two sentences</p>\n<p class="no-margin">are here</p>'),
    (mark_safe('two sentences\nare here'), 'two sentences\nare here'),
])
def test_paragraphs(input, expected):
    assert paragraphs(input) == expected
