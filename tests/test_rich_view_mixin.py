import pytest
from django.db import models

from django_crud.rich_views import RichViewMixin
from django_crud.exceptions import AttrCrudError, SetupCrudError, ReverseCrudError
from .models import Article


def test_getattr():
    class RV(RichViewMixin):
        model = Article
        thing = 'foo'
    rv = RV()
    assert rv.getattr('thing') == 'foo'
    assert rv.getattr('thing2', 'bar') == 'bar'
    with pytest.raises(AttrCrudError):
        rv.getattr('thing2')


def test_getattr_object():
    class Foo:
        bar = 'foo.bar'

    class RV(RichViewMixin):
        model = Article
        object = Foo()
    assert RV().getattr('bar') == 'foo.bar'


@pytest.mark.parametrize('input,expected', [
    (None, []),
    ([{'url': None}], []),
    ([{'url': '/whatever'}], [{'url': '/whatever'}]),
    ([{'url': 'func|make_url'}], [{'url': '/any/where'}]),
])
def test_buttons(input, expected):
    class RV(RichViewMixin):
        model = Article

        def make_url(self):
            return '/any/where'
    rv = RV()
    assert rv.process_buttons(input) == expected


def test_buttons_wrong():
    class RV(RichViewMixin):
        model = Article
    rv = RV()
    assert rv.process_buttons(None) == []
    with pytest.raises(SetupCrudError):
        rv.process_buttons([{'foo': 'bar'}]) == []


def test_buttons_get_absolute_url():
    class Thing(models.Model):
        name = models.CharField()

        def get_absolute_url(self):
            return '/xyz/'

    class RV(RichViewMixin):
        model = Thing
    assert RV().process_buttons([{'url': Thing()}]) == [{'url': '/xyz/'}]


def test_buttons_no_get_absolute_url():
    class Thing(models.Model):
        name = models.CharField()

    class RV(RichViewMixin):
        model = Thing
    with pytest.raises(AttrCrudError):
        RV().process_buttons([{'url': Thing()}])


def test_buttons_drop_down():
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


def test_buttons_rev_exc():
    class RV(RichViewMixin):
        model = Article
    with pytest.raises(ReverseCrudError):
        RV().process_buttons([{'url': 'rev|whatever'}])


def test_buttons_rev(mocker):
    def fake_reverse(viewname, args=None, kwargs=None):
        assert viewname == 'whatever'
        return '/fake_url/'
    mocker.patch('django_crud.rich_views.reverse', fake_reverse)

    class RV(RichViewMixin):
        model = Article
    assert RV().process_buttons([{'url': 'rev|whatever'}]) == [{'url': '/fake_url/'}]
