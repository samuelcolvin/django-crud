import datetime
from decimal import Decimal
import pytest

from django_crud.rich_views import FormatMixin
from django.db import models


@pytest.fixture
def format_mixin():
    return FormatMixin()


def test_callable():
    assert FormatMixin().format_value(lambda: 'called') == 'called'


@pytest.mark.parametrize('v', [None, ''])
def test_none(v):
    assert FormatMixin().format_value(v) == '&mdash;'
    assert FormatMixin().format_value(v) == '&mdash;'


def test_field_choices():
    f = models.IntegerField(choices=[(1, 'one'), (2, 'two')])
    assert FormatMixin().format_value(2, f) == 'two'


def test_field_email():
    f = models.EmailField()
    assert FormatMixin().format_value('test@example.com', f) == ('<a href="mailto:test@example.com" target="blank">'
                                                                 'test@example.com</a>')


def test_field_url():
    f = models.URLField()
    assert FormatMixin().format_value('http://example.com', f) == ('<a href="http://example.com" target="blank">'
                                                                   'http://example.com</a>')


def test_bool():
    assert FormatMixin().format_value(True) == '<span class="glyphicon glyphicon-ok bool"></span>'
    assert FormatMixin().format_value(False) == '<span class="glyphicon glyphicon-remove bool"></span>'


def test_iter():
    assert FormatMixin().format_value(['a', 'b', 'c']) == 'a, b, c'


def test_num():
    assert FormatMixin().format_value(123) == '123'
    assert FormatMixin().format_value(Decimal('123')) == '123'


def test_datetime():
    assert FormatMixin().format_value(datetime.datetime(2015, 4, 3, 13, 47)) == 'April 3, 2015, 1:47 p.m.'


def test_date():
    assert FormatMixin().format_value(datetime.date(2015, 4, 3)) == 'April 3, 2015'


def test_time():
    assert FormatMixin().format_value(datetime.time(13, 47)) == '1:47 p.m.'


def test_str():
    assert FormatMixin().format_value('hello') == 'hello'
