import pytest
from django.db import models

from django_crud.rich_views import RichViewMixin
from django_crud.exceptions import AttrCrudError, SetupCrudError
from .models import Article


def test_rich_view_getattr():
    class RV(RichViewMixin):
        model = Article
        thing = 'foo'
    rv = RV()
    assert rv.getattr('thing') == 'foo'
    assert rv.getattr('thing2', 'bar') == 'bar'
    with pytest.raises(AttrCrudError):
        rv.getattr('thing2')


def test_rich_view_getattr_object():
    class Foo:
        bar = 'foo.bar'

    class RV(RichViewMixin):
        model = Article
        object = Foo()
    rv = RV()
    assert rv.getattr('bar') == 'foo.bar'


def test_rich_view_buttons():
    class RV(RichViewMixin):
        model = Article

        def make_url(self):
            return '/any/where'
    rv = RV()
    assert rv.process_buttons(None) == []
    assert rv.process_buttons([{'url': None}]) == []
    assert rv.process_buttons([{'url': '/whatever'}]) == [{'url': '/whatever'}]
    assert rv.process_buttons([{'url': 'func|make_url'}]) == [{'url': '/any/where'}]


def test_rich_view_buttons_wrong():
    class RV(RichViewMixin):
        model = Article
    rv = RV()
    assert rv.process_buttons(None) == []
    with pytest.raises(SetupCrudError):
        rv.process_buttons([{'foo': 'bar'}]) == []


def test_rich_view_buttons_get_absolute_url():
    class Thing(models.Model):
        name = models.CharField()

        def get_absolute_url(self):
            return '/xyz/'

    class RV(RichViewMixin):
        model = Thing
    rv = RV()
    assert rv.process_buttons([{'url': Thing()}]) == [{'url': '/xyz/'}]


def test_rich_view_buttons_no_get_absolute_url():
    class Thing(models.Model):
        name = models.CharField()

    class RV(RichViewMixin):
        model = Thing
    rv = RV()
    with pytest.raises(AttrCrudError):
        rv.process_buttons([{'url': Thing()}])


def test_rich_view_buttons_drop_down():
    class RV(RichViewMixin):
        model = Article

        def get_dropdown(self):
            return [
                {'url': '/x'},
                {'url': '/y'},
            ]
    rv = RV()
    assert rv.process_buttons([{'dropdown': 'func|get_dropdown'}]) == [{'dropdown': [{'url': '/x'}, {'url': '/y'}]}]
    assert rv.process_buttons([{'dropdown': [{'url': '/a'}]}]) == [{'dropdown': [{'url': '/a'}]}]
