from functools import update_wrapper

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _


class CtrlViewMixin:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.init_handler()
        super(CtrlViewMixin, self).__init__()

    def init_handler(self):
        pass

    @classonlymethod
    def as_view(cls, ctrl, **initkwargs):
        """
        unchanged from super method except for the 4 marked lines below
        """
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError("You tried to pass in the %s method name as a "
                                "keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError("%s() received an invalid keyword %r. as_view "
                                "only accepts arguments that are already "
                                "attributes of the class." % (cls.__name__, key))

        def view(request, *args, **kwargs):
            # { changed
            self = cls(ctrl, **initkwargs)
            self.request = ctrl.request = request
            self.args = ctrl.args = args
            self.kwargs = ctrl.kwargs = kwargs
            # }
            if hasattr(self, 'get') and not hasattr(self, 'head'):
                self.head = self.get
            return self.dispatch(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())
        return view

    def get_context_data(self, **kwargs):
        context = super(CtrlViewMixin, self).get_context_data(**kwargs)
        context.update(**self.ctrl.update_context())
        return context


class GetAttrMixin:
    def getattr(self, name, raise_ex=True):
        if hasattr(self.ctrl, name):
            return getattr(self.ctrl, name)
        return super(GetAttrMixin, self).getattr(name, raise_ex)


class CtrlListView(CtrlViewMixin, ListView):
    def init_handler(self):
        self.ctrl.list_view_init_handler(self)

    def get_queryset(self):
        return self.ctrl.get_queryset()

    def get_detail_url(self, obj):
        return self.ctrl.relative_url('details/{}'.format(obj.pk))


class CtrlDetailView(CtrlViewMixin, DetailView):
    def init_handler(self):
        self.ctrl.detail_view_init_handler(self)

    def get_queryset(self):
        return self.ctrl.get_queryset()


class CtrlCreateView(CtrlViewMixin, CreateView):
    title = _('Create {verbose_name}')

    def init_handler(self):
        self.ctrl.create_view_init_handler(self)

    def form_valid(self, form):
        return self.ctrl.form_valid(self, form)


class CtrlUpdateView(CtrlViewMixin, UpdateView):
    title = _('Update {verbose_name}')

    def init_handler(self):
        self.ctrl.update_view_init_handler(self)

    def form_valid(self, form):
        return self.ctrl.form_valid(self, form)

    def get_queryset(self):
        return self.ctrl.get_queryset()


class RichCtrlListView:
    def get_detail_url(self, obj):
        return self.ctrl.relative_url('details/{}'.format(obj.pk))
