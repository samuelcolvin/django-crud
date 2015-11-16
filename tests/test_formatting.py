import datetime
from decimal import Decimal
import pytest

from django_crud.rich_views import FormatMixin
from django.db import models


@pytest.fixture
def format_mixin():
    return FormatMixin()


def test_callable(format_mixin):
    assert format_mixin.format_value(lambda: 'called') == 'called'


def test_none(format_mixin):
    assert format_mixin.format_value(None) == '&mdash;'
    assert format_mixin.format_value('') == '&mdash;'


def test_field_choices(format_mixin):
    f = models.IntegerField(choices=[(1, 'one'), (2, 'two')])
    assert format_mixin.format_value(2, f) == 'two'


def test_field_email(format_mixin):
    f = models.EmailField()
    assert format_mixin.format_value('test@example.com', f) == ('<a href="mailto:test@example.com" target="blank">'
                                                                'test@example.com</a>')


def test_field_url(format_mixin):
    f = models.URLField()
    assert format_mixin.format_value('http://example.com', f) == ('<a href="http://example.com" target="blank">'
                                                                  'http://example.com</a>')


def test_bool(format_mixin):
    assert format_mixin.format_value(True) == '<span class="glyphicon glyphicon-ok bool"></span>'
    assert format_mixin.format_value(False) == '<span class="glyphicon glyphicon-remove bool"></span>'


def test_iter(format_mixin):
    assert format_mixin.format_value(['a', 'b', 'c']) == 'a, b, c'


def test_num(format_mixin):
    assert format_mixin.format_value(123) == '123'
    assert format_mixin.format_value(Decimal('123')) == '123'


def test_datetime(format_mixin):
    assert format_mixin.format_value(datetime.datetime(2015, 4, 3, 13, 47)) == 'April 3, 2015, 1:47 p.m.'


def test_date(format_mixin):
    assert format_mixin.format_value(datetime.date(2015, 4, 3)) == 'April 3, 2015'


def test_time(format_mixin):
    assert format_mixin.format_value(datetime.time(13, 47)) == '1:47 p.m.'


def test_str(format_mixin):
    assert format_mixin.format_value('hello') == 'hello'
