from django_crud.forms import RichCrudForm
import re

from django.contrib import messages
from django.conf.urls import url, include
from django.db.models import ProtectedError
from django.forms import modelform_factory, ModelForm
from django.shortcuts import redirect
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _

from .rich_views import RichListViewMixin, RichDetailViewMixin, RichCreateViewMixin, RichUpdateViewMixin, \
    RichDeleteViewMixin
from .base_views import CtrlListView, CtrlDetailView, CtrlCreateView, CtrlUpdateView, CtrlDeleteView


class VanillaController:
    model = None

    list_template_name = None
    detail_template_name = None
    create_template_name = None
    update_template_name = None
    modal_edit_template_name = None
    delete_template_name = None

    form_factory_kwargs = {
        'exclude': ('id',)  # either fields or exclude are required these days
    }

    def __init__(self):
        self.request = self.args = self.kwargs = None

    def get_queryset(self):
        return self.model.objects.all()

    def update_context(self):
        return {}

    @property
    def list_view_parents(self):
        return CtrlListView,

    def list_view_init_handler(self, view_cls):
        pass

    def list_view(self):
        class TmpListView(*self.list_view_parents):
            model = self.model
            template_name = self.list_template_name
        return TmpListView.as_view(self)

    @property
    def detail_view_parents(self):
        return CtrlDetailView,

    def detail_view_init_handler(self, view_cls):
        pass

    def detail_view(self):
        class TmpDetailView(*self.detail_view_parents):
            model = self.model
            template_name = self.detail_template_name
        return TmpDetailView.as_view(self)

    @property
    def form_parents(self):
        return ModelForm

    def form_factory(self):
        return modelform_factory(self.model, form=self.form_parents, **self.form_factory_kwargs)

    def get_create_success_url(self):
        return self.relative_url('list')

    def create_form_valid(self, view, form):
        view.object = form.save()
        return redirect(self.get_create_success_url())

    @property
    def create_view_parents(self):
        return CtrlCreateView,

    def create_view_init_handler(self, view_cls):
        pass

    def create_view(self):
        class TmpCreateView(*self.create_view_parents):
            form_class = self.form_factory()
            model = self.model
            template_name = self.create_template_name
            modal_template_name = self.modal_edit_template_name  # TODO
        return TmpCreateView.as_view(self)

    @property
    def update_view_parents(self):
        return CtrlUpdateView,

    def get_update_success_url(self):
        return self.relative_url('details/{pk}'.format(**self.kwargs))

    def update_form_valid(self, view, form):
        view.object = form.save()
        return redirect(self.get_update_success_url())

    def update_view_init_handler(self, view_cls):
        pass

    def update_view(self):
        class TmpUpdateView(*self.update_view_parents):
            form_class = self.form_factory()
            model = self.model
            template_name = self.update_template_name
            modal_template_name = self.modal_edit_template_name  # TODO
        return TmpUpdateView.as_view(self)

    @property
    def delete_view_parents(self):
        return CtrlDeleteView,

    def get_delete_success_url(self):
        return self.get_create_success_url()

    def delete_object(self, object):
        try:
            object.delete()
        except ProtectedError:
            messages.error(self.request, _('Sorry, this object is in use so it cannot be deleted.'))

    def delete_view_init_handler(self, view_cls):
        pass

    def delete_view(self):
        class TmpDeleteView(*self.delete_view_parents):
            model = self.model
            template_name = self.delete_template_name
            modal_template_name = self.modal_edit_template_name  # TODO
        return TmpDeleteView.as_view(self)

    @classonlymethod
    def as_views(cls, name_prefix):
        ctrl = cls()
        url_patterns = []

        list_view = ctrl.list_view and ctrl.list_view()
        if list_view:
            url_patterns.append(url(r'list/$', list_view, name='%s-list' % name_prefix))

        detail_view = ctrl.detail_view and ctrl.detail_view()
        if detail_view:
            url_patterns.append(url(r'details/(?P<pk>\d+)/$', detail_view, name='%s-details' % name_prefix))

        create_view = ctrl.create_view and ctrl.create_view()
        if create_view:
            url_patterns.append(url(r'create/$', create_view, name='%s-create' % name_prefix))

        update_view = ctrl.update_view and ctrl.update_view()
        if update_view:
            url_patterns.append(url(r'update/(?P<pk>\d+)/$', update_view, name='%s-update' % name_prefix))

        delete_view = ctrl.delete_view and ctrl.delete_view()
        if delete_view:
            url_patterns.append(url(r'delete/(?P<pk>\d+)/$', delete_view, name='%s-delete' % name_prefix))

        return include(url_patterns)

    def relative_url(self, rel_url):
        new_url_ending = '/%s/' % rel_url.strip('/')
        return re.sub('/(list|details/\d+|create|update/\d+|delete/\d+)/$', new_url_ending, self.request.path)


# noinspection PyMethodMayBeStatic
class RichController(VanillaController):
    list_template_name = 'crud/table_list.jinja'
    detail_template_name = 'crud/details.jinja'
    create_template_name = update_template_name = 'crud/edit.jinja'
    delete_template_name = 'crud/delete.jinja'
    list_view_buttons = [
        'func|create_item_button'
    ]
    list_display_items = []
    detail_display_items = []

    detail_view_buttons = [
        'func|update_item_button',
        'func|delete_item_button',
    ]

    def list_view_init_handler(self, view_cls):
        view_cls.buttons = self.list_view_buttons
        view_cls.display_items = self.list_display_items

    @property
    def list_view_parents(self):
        return RichListViewMixin, CtrlListView

    @property
    def detail_view_parents(self):
        return RichDetailViewMixin, CtrlDetailView

    def detail_view_init_handler(self, view_cls):
        view_cls.buttons = self.detail_view_buttons
        view_cls.display_items = self.detail_display_items

    @property
    def form_parents(self):
        return RichCrudForm

    @property
    def create_view_parents(self):
        return RichCreateViewMixin, CtrlCreateView

    def create_item_button(self):
        return self.relative_url('create')
    create_item_button.short_description = _('Create {verbose_name}')

    @property
    def update_view_parents(self):
        return RichUpdateViewMixin, CtrlUpdateView

    def update_item_button(self):
        return self.relative_url('update/{pk}'.format(**self.kwargs))
    update_item_button.short_description = _('Update {verbose_name}')

    @property
    def delete_view_parents(self):
        return RichDeleteViewMixin, CtrlDeleteView

    def delete_item_button(self):
        return self.relative_url('delete/{pk}'.format(**self.kwargs))
    delete_item_button.short_description = _('Delete {verbose_name}')
