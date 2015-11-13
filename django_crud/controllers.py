import re
from django.forms import modelform_factory
from django.shortcuts import redirect
from django.utils.decorators import classonlymethod
from django.utils.encoding import force_text
from django.conf.urls import url, include
from django.utils.translation import ugettext_lazy as _

from .plumbing import ButtonMixin, ItemDisplayMixin
from .base_views import GetAttrMixin, CtrlListView, CtrlDetailView, CtrlCreateView, CtrlUpdateView, RichCtrlListView


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
        return CtrlListView,

    def list_view_init_handler(self, view_cls):
        pass

    def list_view(self):
        print(repr(self.list_view_parents))
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

    def update_view_init_handler(self, view_cls):
        pass

    def update_view(self):
        class TmpUpdateView(*self.update_view_parents):
            form_class = self.form_factory()
            model = self.model
            template_name = self.update_template_name
            modal_template_name = self.modal_edit_template_name  # TODO
        return TmpUpdateView.as_view(self)

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
        'create_item_button'
    ]
    list_display_items = []

    detail_view_buttons = [
        'create_item_button',
        # 'edit_item_button',
    ]

    def list_view_init_handler(self, view_cls):
        view_cls.buttons = self.list_view_buttons
        view_cls.display_items = self.list_display_items

    @property
    def list_view_parents(self):
        return RichCtrlListView, GetAttrMixin, ItemDisplayMixin, CtrlListView

    def detail_view_init_handler(self, view_cls):
        view_cls.buttons = self.detail_view_buttons

    @property
    def detail_view_parents(self):
        return GetAttrMixin, ItemDisplayMixin, CtrlDetailView

    @property
    def create_view_parents(self):
        return ButtonMixin, CtrlCreateView

    def create_item_button(self):
        return self.relative_url('create')
    create_item_button.short_description = _('Create {verbose_name}')
