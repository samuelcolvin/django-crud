import pytest
from django_crud.controllers import RichController
from .models import Article


class ArticleController(RichController):
    model = Article


@pytest.fixture
def views():
    urlconf_module, _, _ = ArticleController.as_views('test')
    return urlconf_module


def assert_contains(r, text):
    assert r.status_code == 200
    r.render()
    assert text in r.content.decode(), '"{}" not found in response'.format(text)


def assert_not_contains(r, text):
    assert r.status_code == 200
    r.render()
    assert text not in r.content.decode(), '"{}" unexpectedly found in response'.format(text)


def test_list_view_empty_empty(db, views, request):
    list_view = views[0]
    r = list_view.callback(request('/article/list/'))
    assert_contains(r, '<h3>No Articles found</h3>')
    assert_not_contains(r, '<a href="/article/details/')


def test_list_view_2_articles(db, views, request):
    assert Article.objects.count() == 0
    art1 = Article.objects.create(title='article 1', body='this is the first body')
    art2 = Article.objects.create(title='article 2', body='this is the first body', slug='article_2')
    list_view = views[0]
    r = list_view.callback(request('/article/list/'))
    assert_not_contains(r, '<h3>No Articles found</h3>')
    assert_contains(r, '<a href="/article/details/{}/">article 1</a>'.format(art1.id))
    assert_contains(r, '<a href="/article/details/{}/">article 2</a>'.format(art2.id))
