import datetime
import logging
from functools import update_wrapper
from decimal import Decimal

from django.core.urlresolvers import reverse, NoReverseMatch
from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from django.utils.decorators import classonlymethod
from django.utils.safestring import mark_safe, SafeBytes
from django.utils.html import escape
from django.utils.functional import cached_property
from django.utils.formats import date_format, time_format, number_format

from .exceptions import AttrCrudError, SetupCrudError

logger = logging.getLogger('django')


def maybe_call(value_or_func, *args, **kwargs):
    return value_or_func(*args, **kwargs) if callable(value_or_func) else value_or_func


class ButtonMixin:
    buttons = []

    def back_url(self):
        return self.request.META.get('HTTP_REFERER')

    def getattr(self, name, alt=AttrCrudError):
        if hasattr(self, name):
            return getattr(self, name)
        elif hasattr(self, 'object'):
            return getattr(self.object, name)
        elif issubclass(alt, Exception):
            raise alt('%s not found on %s instance or self.object' % (name, self.__class__.__name__))
        else:
            return None

    def check_show_button(self, button):
        if button is None or ('url' in button and button['url'] is None):
            return False
        if not isinstance(button, dict):
            return True
        if 'show_if' not in button:
            return True
        if button['show_if'] in {True, False}:
            return button['show_if']
        show_if = self.getattr(button['show_if'])
        return bool(maybe_call(show_if))

    def process_buttons(self, button_group):
        if not button_group:
            return []
        if isinstance(button_group, list):
            return [self.process_buttons(button) for button in button_group if self.check_show_button(button)]
        return self.process_button(button_group)

    def get_url(self, text):
        if text.startswith('func|'):
            text = text.split('|')[1]
        value = maybe_call(self.getattr(text))

        if isinstance(value, models.Model):
            if hasattr(value, 'get_absolute_url'):
                return value.get_absolute_url()
            else:
                raise AttrCrudError('Model instance "{!r}" has no "get_absolute_url" method'.format(value))
        return value

    def process_button(self, button):
        if isinstance(button, str):
            button = {
                'text': self.get_sub_attr(button) or button,
                'url': button,
            }
        elif isinstance(button, tuple):
            if len(button) != 2:
                raise SetupCrudError('tuple button definitions should have 2 elements, got: {!r}'.format(button))
            button = {
                'text': button[0],
                'url': button[1],
            }

        if 'url' in button:
            button['url'] = self.get_url(button['url'])
        elif 'dropdown' in button:
            if isinstance(button['dropdown'], str) and button['dropdown'].startswith('func|'):
                fname = button['dropdown'].split('|', 1)[1]
                button['dropdown'] = self.getattr(fname)()
            button['dropdown'] = map(self.process_button, button['dropdown'])
        else:
            raise SetupCrudError('neither "url" nor "dropdown" found in button: {!r}'.format(button))
        return button

    def get_sub_attr(self, attr_name, obj=None, prop_name='short_description'):
        """
        get a property of an object's attribute by name.
        :param obj: object to look at
        :param attr_name: name to get short_description for
        :param prop_name: name of property to get, typically "short_description"
        :return: property value or None
        """
        if obj:
            attr = getattr(obj, attr_name, None)
        else:
            attr = self.getattr(attr_name, None)

        if attr:
            v = getattr(attr, prop_name, None)
            if v is not None:
                return v.format(verbose_name=self.model._meta.verbose_name)

    def _process_local_function(self, field_info, obj):
        return getattr(self, field_info.attr_name)(obj)

    def get_buttons(self):
        return self.buttons

    def get_context_data(self, **kwargs):
        kwargs['buttons'] = self.process_buttons(self.get_buttons()),
        return super(ButtonMixin, self).get_context_data(**kwargs)


RENDER_MAILTO = getattr(settings, 'RENDER_MAILTO', True)


# noinspection PyMethodMayBeStatic
class FormatMixin:
    """
    General purpose mixin for converting virtually anything to a string intelligently.

    Reasonable defaults are provided, but most thing scan be changed.
    """

    def fmt_none_empty(self, value):
        return mark_safe('&mdash;')

    def fmt_field_choices(self, value, field):
        choice_dict = dict(field.choices)
        return choice_dict.get(value, value)

    def fmt_email_field(self, value):
        if RENDER_MAILTO:
            return mark_safe('<a href="mailto:{0}" target="blank">{0}</a>'.format(escape(value)))
        else:
            return value

    def fmt_url_field(self, value):
        return mark_safe('<a href="{0}" target="blank">{0}</a>'.format(escape(value)))

    def fmt_bool(self, value):
        icon = 'ok' if value else 'remove'
        return mark_safe('<span class="glyphicon glyphicon-{} bool"></span>'.format(icon))

    def fmt_iter(self, value):
        return ', '.join(map(self.format_value, value))

    def fmt_number(self, value):
        return number_format(value)

    def fmt_datetime(self, value):
        return date_format(value, 'DATETIME_FORMAT')

    def fmt_date(self, value):
        return date_format(value)

    def fmt_time(self, value):
        return time_format(value, 'TIME_FORMAT')

    def format_value(self, value, field=None):
        if callable(value):
            value = value()
        elif value in (None, ''):
            return self.fmt_none_empty(value)
        elif field and len(field.choices) > 0:
            return self.fmt_field_choices(value, field)
        elif isinstance(field, models.EmailField):
            return self.fmt_email_field(value)
        elif isinstance(field, models.URLField):
            return self.fmt_url_field(value)
        elif isinstance(value, bool):
            return self.fmt_bool(value)
        elif isinstance(value, (list, tuple, QuerySet)):
            return self.fmt_iter(value)
        elif isinstance(value, (Decimal, float, int)):
            return self.fmt_number(value)
        elif isinstance(value, datetime.datetime):
            return self.fmt_datetime(value)
        elif isinstance(value, datetime.date):
            return self.fmt_date(value)
        elif isinstance(value, datetime.time):
            return self.fmt_time(value)
        return value


class ItemDisplayMixin(FormatMixin, ButtonMixin):
    """
    ItemDisplayMixin works with ListView and DetailView to simplify the process of listing and displaying a model.

    This class should be "mixed in" before ListView or DetailView so it can override their attributes.
    """

    #: an instance of django.db.models.Model to be displayed, this is already required for ListView or DetailView
    model = None

    title = None

    #: list of references to attributes of instances of the model, items maybe
    #: * field names
    #: * references to related fields either using Django's "thing__related_ob" syntax or "thing.related_ob" syntax
    #: * references to functions in the class, they should be identified by "func|name_of_function" the function
    #:   should take an instance of the model as it's only argument as in "def name_of_function(self, obj):..."
    #: * pattern for a reverse link to a page in the form at "rev|view-name|field_or_func" field_or_func
    #:   may be any of the above options eg. "thing__related_ob", "thing.related_ob" or "func|name_of_function"
    #: * any of the above may be the second value in a tuple where the first value is a verbose name
    #:   to use for the field if you don't like it's standard verbose name.
    display_items = []

    #: subset of display_items which are considered "long" eg. TextField's which should be displayed
    #: full width not in columns, if in long_items an attribute will be yielded by gen_object_long
    #: otherwise by gen_object_short
    long_items = []

    #: field to order the model by, if None no ordering is performed here
    order_by = None

    #: number of items to show on each each page
    paginate_by = 20

    #: name of view showing details of the model suitable for passing to reverse
    #: this is passed to the template and may be left blank when this actually is a detail view
    detail_view = None

    #: whether to filter AttributeValue's on list_show = True
    filter_show_list = False

    column_css = {}

    _LOCAL_FUNCTION = 'func!'

    def __init__(self):
        self._model_meta = self.model._meta
        self._field_names = [f.name for f in self._model_meta.fields]
        self._extra_attrs = []

    def get_context_data(self, **kwargs):
        """
        Overrides standard the standard get_context_data to provide the following in the context:
            gen_object_short: generator for short attributes of each item
            gen_object_long: generator for long attributes of each item
            get_item_title: returns the title of any object
            plural_name: the plural name of the model
            title: if not already set is set to plural_name
            detail_view: from above

        :param kwargs: standard get_context_data kwargs
        :return: the context
        """
        context = super(ItemDisplayMixin, self).get_context_data(**kwargs)
        plural_name = self._model_meta.verbose_name_plural
        context.update(
            gen_object_short=self.gen_object_short,
            gen_object_short_with_column=self.gen_object_short_with_column,
            column_css=self.column_css,
            gen_object_long=self.gen_object_long,
            get_item_title=self.get_item_title,
            plural_name=plural_name,
            title=self.get_title() or plural_name,
            detail_view=getattr(self, 'get_detail_view_url', lambda: self.detail_view)(),
        )
        return context

    def get_title(self):
        return self.title

    def get_queryset(self):
        """
        Overrides standard the standard get_queryset to order the qs and call select_related.
        :return:
        """
        qs = super(ItemDisplayMixin, self).get_queryset()
        if self.order_by:
            qs = qs.order_by(*self.order_by)
        return qs

    def gen_object_short(self, obj, inc_help_text=False):
        """
        Generator of (name, value) pairs which are short for a given object.

        :param obj: the object to to find generate attributes for
        :param inc_help_text: whether or not to yield help text as middle value of the tuple
        :return: list of (name, value) or (name, help_text, value) pairs which are short.
        """
        for field_info in self._item_info:
            if not field_info.is_long:
                yield self._display_value(obj, field_info, inc_help_text)

    def gen_object_short_with_column(self, obj):
        """
        Generator of (column, name, value) pairs which are short for a given object.

        :yield: (column, name, value).
        """
        for col, (name, value) in zip(self.get_display_items(), self.gen_object_short(obj)):
            col_name = col
            if isinstance(col, tuple):
                col_name = col[1]
            css_classes = self.column_css.get(col_name, '')
            yield col, name, value, css_classes

    def gen_object_long(self, obj, inc_help_text=False):
        """
        Generator of (name, value) pairs which are long for a given object.

        :param obj: the object to to find generate attributes for
        :param inc_help_text: whether or not to yield help text as middle value of the tuple
        :return: list of (name, value) pairs which are long.
        """
        for field_info in self._item_info:
            if field_info.is_long:
                yield self._display_value(obj, field_info, inc_help_text)

    def get_item_title(self, obj):
        """
        returns the title of an instance of model, the default is dumb and just calls str. But can be
        override to provide more intelligent functionality.

        This is made available in the context to be used in templates.

        :param obj: an instance of model.
        :return: it's title (or name)
        """
        return str(obj)

    @cached_property
    def _item_info(self):
        """
        Returns a list of FieldInfo instances.

        After the first call the list is cached to improve performance.
        :return: list of tuples for each item in display_items
        """
        return map(self._getattr_info, self._all_display_items)

    def get_display_items(self):
        """
        return display items. Override to conditionally alter display items list.
        :return: list of (short) items to display
        """
        return self.display_items

    @cached_property
    def _all_display_items(self):
        """
        all items to show from both display_items and long_items.
        """
        display_items = tuple(self.get_display_items())
        check_disp_items = [item[1] if isinstance(item, tuple) else item for item in display_items]
        return display_items + tuple(filter(lambda i: i not in check_disp_items, self.long_items))

    def _getattr_info(self, attr_name):
        """
        Finds the values for each tuple returned by _item_info.

        :param attr_name: value direct from display_items
        :return: FieldInfo instance
        """
        field_info = FieldInfo(attr_name, long_items=self.long_items)
        if isinstance(field_info.attr_name, tuple):
            if len(field_info.attr_name) == 2:
                field_info.verbose_name, field_info.attr_name = field_info.attr_name
            elif len(field_info.attr_name) == 3:
                field_info.verbose_name, field_info.attr_name, field_info.help_text = field_info.attr_name
            else:
                raise Exception('display_item tuples must be 2 or 3 in length, not %d' % len(field_info.attr_name))

        if field_info.attr_name.startswith('rev|'):
            parts = field_info.attr_name.split('|', 2)
            _, field_info.rev_view_name, field_info.attr_name = parts

        if field_info.attr_name.startswith('func|'):
            field_info.attr_name = field_info.attr_name.split('|')[1]
            field_info.field = self._LOCAL_FUNCTION
            if field_info.verbose_name is None:
                field_info.verbose_name = self.get_sub_attr(field_info.attr_name)
                field_info.verbose_name = field_info.verbose_name or field_info.attr_name
            return field_info

        model, meta, field_names = self.model, self._model_meta, self._field_names
        attr_name_part = None
        for attr_name_part in self._split_attr_name(field_info.attr_name):
            if attr_name_part in field_names:
                field_info.field = meta.get_field_by_name(attr_name_part)[0]
                if field_info.field.rel:
                    model = field_info.field.rel.to
                    meta = model._meta
                    field_names = [f.name for f in meta.fields]

        # find verbose name if it's None so far
        if field_info.verbose_name is None:
            # priority_short_description has priority over field.verbose_name even when it's on a related model
            field_info.verbose_name = self.get_sub_attr(attr_name_part, model, 'priority_short_description')
            if not field_info.verbose_name:
                if field_info.field:
                    field_info.verbose_name = field_info.field.verbose_name
                else:
                    field_info.verbose_name = self.get_sub_attr(attr_name_part, model)
                if not field_info.verbose_name:
                    field_info.verbose_name = field_info.attr_name

        # find help text if it's None so far
        if field_info.help_text is None:
            field_info.help_text = self.get_sub_attr(attr_name_part, model, 'priority_help_text')
            if not field_info.help_text:
                if field_info.field:
                    field_info.help_text = field_info.field.help_text
                else:
                    field_info.help_text = self.get_sub_attr(attr_name_part, model, 'help_text')
        return field_info

    @staticmethod
    def _split_attr_name(attr_name):
        """
        split an attribute name either on '__' or '.'
        """
        return attr_name.replace('__', '.').split('.')

    def _display_value(self, obj, field_info, inc_help_text=False):
        """
        Generates a value for an attribute, optionally generate it's url and make it a link and returns it
        together with with it's verbose name.

        If the attribute name refers to a function the value is returned raw (after reversing if rev_view_name,
        otherwise it's processed by convert_to_string.

        :param obj: any instance of the model to get the value from.
        :param field_info: is FieldInfo below
        :param inc_help_text: whether or not to return help text as middle value of the tuple
        :return: tuple containing (verbose_name, help_text, value)
        """
        if field_info.field == self._LOCAL_FUNCTION:
            value = self.getattr(field_info.attr_name)(obj)
        else:
            value = self._get_object_value(obj, field_info.attr_name)
        url = None
        if field_info.rev_view_name and hasattr(value, 'pk'):
            rev_tries = [
                {'viewname': field_info.rev_view_name},
                {'viewname': field_info.rev_view_name, 'args': (value.pk,)},
            ]
            for rev_try in rev_tries:
                try:
                    url = reverse(**rev_try)
                except NoReverseMatch:
                    pass
                else:
                    break
            if url is None:
                logger.error('No reverse found for "%s"' % field_info.rev_view_name)

        if field_info.field != self._LOCAL_FUNCTION:
            value = self.convert_to_string(value, field_info.field)

        if field_info.rev_view_name and url:
            value = mark_safe('<a href="%s">%s</a>' % (url, escape(value)))

        # Ensure returning unicode.
        if isinstance(value, str) and not isinstance(value, SafeBytes):
            value = str(value)
        if inc_help_text:
            return field_info.verbose_name, field_info.help_text, value
        else:
            return field_info.verbose_name, value

    def _get_object_value(self, obj, attr_name):
        """
        Chomp through attribute names from display_items to get the attribute or related attribute
        from the object

        :param obj: the object to find the attribute for
        :param attr_name: the attribute name
        :return: the attribute
        """
        for b in self._split_attr_name(attr_name):
            if obj:
                obj = getattr(obj, b)
        return obj


class FieldInfo(object):
    """
    Simple namespace for information about fields.

    field: the type of the field of the attribute, 'func!' if it's a function
    attr_name: the attribute name from display_items
    verbose_name: the verbose name of that field
    help_text: help text for this field, None if not supplied
    rev_view_name: view name to reverse to get item url, None if no reverse link
    is_long: boolean indicating if the field should be considered "long" (eg. is in long_items)
    """
    field = None
    verbose_name = None
    help_text = None
    rev_view_name = None

    def __init__(self, attr_name, long_items):
        self.attr_name = attr_name
        self._long_items = set(long_items)
        for item in long_items:
            if item.startswith('func|'):
                self._long_items.add(item.replace('func|', ''))

    @cached_property
    def is_long(self):
        return self.attr_name in self._long_items


class CtrlViewMixin:
    ctrl = None

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


class CtrlItemDisplayMixin(ItemDisplayMixin, CtrlViewMixin):
    def getattr(self, name, raise_ex=True):
        if hasattr(self.ctrl, name):
            return getattr(self.ctrl, name)
        return super(CtrlItemDisplayMixin, self).getattr(name, raise_ex)
