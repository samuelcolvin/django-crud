import re
from django.forms import modelform_factory
from django.shortcuts import redirect
from django.utils.decorators import classonlymethod
from django.utils.encoding import force_text
from django.views.generic import DetailView, ListView, CreateView
from django.conf.urls import url, include
from django.utils.translation import ugettext_lazy as _

from .base_views import CtrlViewMixin, CtrlItemDisplayMixin, CtrlListView


class VanillaController:
    model = None

    list_template_name = None
    detail_template_name = None
    create_template_name = None
    update_template_name = None
    modal_edit_template_name = None
    delete_template_name = None

    success_url = None

    form_factory_kwargs = {
        'exclude': ('id',)  # either fields or exclude is required these days
    }

    def get_queryset(self):
        return self.model.objects.all()

    def update_context(self):
        return {}

    @property
    def list_view_parents(self):
        return CtrlViewMixin, ListView

    def list_view_init_handler(self, view_cls):
        pass

    def list_view(self):
        class TmpListView(*self.list_view_parents):
            model = self.model
            template_name = self.list_template_name

            def __init__(self, ctrl):
                # allow extra properties to be set without overriding this entire method
                self.ctrl = ctrl
                ctrl.list_view_init_handler(self)
                super(TmpListView, self).__init__()

            def get_queryset(self):
                return self.ctrl.get_queryset()

        return TmpListView.as_view(self)

    @property
    def detail_view_parents(self):
        return CtrlViewMixin, DetailView

    def detail_view_init_handler(self, view_cls):
        pass

    def detail_view(self):
        class TmpDetailView(*self.detail_view_parents):
            model = self.model
            template_name = self.detail_template_name

            def __init__(self, ctrl):
                self.ctrl = ctrl
                ctrl.detail_view_init_handler(self)
                super(TmpDetailView, self).__init__()

            def get_queryset(self):
                return self.ctrl.get_queryset()

        return TmpDetailView.as_view(self)

    def form_factory(self):
        return modelform_factory(self.model, **self.form_factory_kwargs)

    def get_success_url(self, view):
        """
        Get URL to redirect

        :param view: current view
        :return: None
        """
        if self.success_url:
            return force_text(self.success_url)
        else:
            return self.relative_url('list')

    def form_valid(self, view, form):
        view.object = form.save()
        return redirect(self.get_success_url(view))

    @property
    def create_view_parents(self):
        return CtrlViewMixin, CreateView

    def create_view_init_handler(self, view_cls):
        pass

    def create_view(self):
        class TmpCreateView(*self.create_view_parents):
            form_class = self.form_factory()
            model = self.model
            template_name = self.create_template_name
            modal_template_name = self.modal_edit_template_name  # TODO

            def __init__(self, ctrl):
                self.ctrl = ctrl
                ctrl.create_view_init_handler(self)
                super(TmpCreateView, self).__init__()

            def form_valid(self, form):
                return self.ctrl.form_valid(self, form)

        return TmpCreateView.as_view(self)

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

        # url_patterns = [
        #     url(r'edit/(?P<pk>\d+)/$', ctrl.update_view(), name='%s-edit' % cls.name_prefix),
        #     url(r'delete/(?P<pk>\d+)/$', ctrl.delete_view(), name='%s-delete' % cls.name_prefix),
        # ]
        return include(url_patterns)

    def relative_url(self, rel_url):
        return re.sub('/(list|details/\d+|create|update/\d+|delete/\d+)/$', '/%s/' % rel_url, self.request.path)


# noinspection PyMethodMayBeStatic
class RichController(VanillaController):
    list_template_name = 'crud/table_list.jinja'
    detail_template_name = 'crud/details.jinja'
    create_template_name = update_template_name = 'crud/edit.jinja'
    list_view_buttons = [
        'add_item_button'
    ]
    list_display_items = []

    detail_view_buttons = [
        # 'add_item_button',
        # 'edit_item_button',
    ]

    def list_view_init_handler(self, view_cls):
        view_cls.buttons = self.list_view_buttons
        view_cls.display_items = self.list_display_items

    @property
    def list_view_parents(self):
        return CtrlListView, ListView

    def detail_view_init_handler(self, view_cls):
        view_cls.buttons = self.detail_view_buttons

    @property
    def detail_view_parents(self):
        return CtrlItemDisplayMixin, DetailView

    def add_item_button(self):
        return self.relative_url('create')
    add_item_button.short_description = _('Add {verbose_name}')
