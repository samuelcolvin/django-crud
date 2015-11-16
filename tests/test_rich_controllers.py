import re
import pytest
from django_crud.controllers import RichController
from .models import Article


class ArticleController(RichController):
    model = Article


@pytest.fixture
def views():
    urlconf_module, _, _ = ArticleController.as_views('test')
    return urlconf_module


def remove_spaces(html):
    html = re.sub('\n +', '\n', html)
    html = re.sub(' {2,}', ' ', html)
    html = re.sub('\n{2,}', '\n', html)
    return html


def assert_contains(r, text, status_code=200, html=False):
    assert r.status_code == status_code
    r.render()
    content = r.content.decode()
    if html:
        content = remove_spaces(content)
    assert text in content, '"{}" not found in response'.format(text)


def assert_not_contains(r, text, status_code=200, html=False):
    assert r.status_code == status_code
    r.render()
    content = r.content.decode()
    if html:
        content = remove_spaces(content)
    assert text not in content, '"{}" unexpectedly found in response'.format(text)


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
    assert_contains(r, '<a href="/article/details/{}/">article 1</a>'.format(art1.id))
    assert_contains(r, '<a href="/article/details/{}/">article 2</a>'.format(art2.id))
    assert_contains(r, '<a href="/article/create/" class="btn btn-default ">Create Article</a>')
    assert_not_contains(r, '<h3>No Articles found</h3>')
    assert_not_contains(r, 'Update Article')
    assert_not_contains(r, 'Delete Article')


def test_detail_view(db, views, request):
    assert Article.objects.count() == 0
    art1 = Article.objects.create(title='article 1', body='this is the first body')
    detail_view = views[1]
    r = detail_view.callback(request('/article/details/%d/' % art1.id), pk=art1.pk)
    assert_contains(r, '<div class="one-line detail-info">\narticle 1\n</div>', html=True)
    assert_contains(r, '<a href="/article/update/1/" class="btn btn-default ">Update Article</a>')
    assert_contains(r, '<a href="/article/delete/1/" class="btn btn-default ">Delete Article</a>')
