import pytest
from django.test import RequestFactory
from django_crud.controllers import RichController
from .models import Article


class ArticleController(RichController):
    model = Article


@pytest.fixture
def views():
    urlconf_module, _, _ = ArticleController.as_views('test')
    return urlconf_module


@pytest.fixture
def request():
    def request_factory(url='/'):
        return RequestFactory().get(url)
    return request_factory


def test_list_view(db, views, request):
    list_view = views[0]
    r = list_view.callback(request())
    assert r.status_code == 200
    # can't render as we need a template
    print(r.render())
