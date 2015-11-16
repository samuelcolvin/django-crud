import pytest

from django_crud.base_views import CtrlListView
from django_crud.controllers import VanillaController
from .models import Article


class VanArticleController(VanillaController):
    model = Article


def test_controller_init():
    c = VanillaController()
    assert c.list_view_parents == (CtrlListView,)


def test_controller_init_as_views():
    urlconf_module, app_name, namespace = VanArticleController.as_views('test')
    assert len(urlconf_module) == 5

    list_view = urlconf_module[0]
    assert list_view.name == 'test-list'
    assert list_view.regex.pattern == 'list/$'

    detail_view = urlconf_module[1]
    assert detail_view.name == 'test-details'
    assert detail_view.regex.pattern == 'details/(?P<pk>\d+)/$'

    create_view = urlconf_module[2]
    assert create_view.name == 'test-create'
    assert create_view.regex.pattern == 'create/$'

    update_view = urlconf_module[3]
    assert update_view.name == 'test-update'
    assert update_view.regex.pattern == 'update/(?P<pk>\d+)/$'

    delete_view = urlconf_module[4]
    assert delete_view.name == 'test-delete'
    assert delete_view.regex.pattern == 'delete/(?P<pk>\d+)/$'


def test_controller_init_as_views_instance():
    with pytest.raises(AttributeError):
        VanArticleController().as_views('test')
