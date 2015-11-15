import datetime
import logging
from decimal import Decimal

from django.core.urlresolvers import reverse, NoReverseMatch
from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.functional import cached_property
from django.utils.formats import date_format, time_format, number_format
from django.utils.translation import ugettext_lazy as _

from .exceptions import AttrCrudError, SetupCrudError, ReverseCrudError

logger = logging.getLogger('django')


def maybe_call(value_or_func, *args, **kwargs):
    return value_or_func(*args, **kwargs) if callable(value_or_func) else value_or_func


class RichViewMixin:
    buttons = []
    title = None

    def back_url(self):
        return self.request.META.get('HTTP_REFERER')

    def getattr(self, name, alt=AttrCrudError):
        if hasattr(self, name):
            return getattr(self, name)
        elif hasattr(self, 'object'):
            return getattr(self.object, name)
        elif isinstance(alt, type) and issubclass(alt, Exception):
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
        if not isinstance(button_group, (dict, str)):
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

    @cached_property
    def label_ctx(self):
        return dict(
            verbose_name=self.model._meta.verbose_name,
            verbose_name_plural=self.model._meta.verbose_name_plural,
        )

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
                return v.format(**self.label_ctx)

    def _process_local_function(self, field_info, obj):
        return getattr(self, field_info.attr_name)(obj)

    def get_buttons(self):
        return self.buttons

    def get_context_data(self, **kwargs):
        kwargs.update(
            buttons=self.process_buttons(self.get_buttons()),
            title=self.get_title(),
            model_name=self.model._meta.verbose_name,
            plural_model_name=self.model._meta.verbose_name_plural,
        )
        return super(RichViewMixin, self).get_context_data(**kwargs)

    def get_title(self):
        return self.title.format(**self.label_ctx) if self.title else self.model._meta.verbose_name_plural


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


class ItemDisplayMixin(FormatMixin, RichViewMixin):
    """
    ItemDisplayMixin works with ListView and DetailView to simplify the process of listing and displaying a model.

    This class should be "mixed in" before ListView or DetailView so it can override their attributes.
    """

    #: an instance of django.db.models.Model to be displayed, this is already required for ListView or DetailView
    model = None

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
    #: full width not in columns, long_items will be yielded by gen_object_long
    #: otherwise by gen_object_short

    #: field to order the model by, if None no ordering is performed here
    order_by = None

    #: number of items to show on each each page
    paginate_by = 20

    extra_field_info = {}

    def __init__(self, *args, **kwargs):
        self._field_names = [f.name for f in self.model._meta.fields]
        self._extra_attrs = []
        super(ItemDisplayMixin, self).__init__(*args, **kwargs)

    def get_queryset(self):
        """
        Overrides standard the standard get_queryset to order the qs and call select_related.
        :return:
        """
        qs = super(ItemDisplayMixin, self).get_queryset()
        if self.order_by:
            qs = qs.order_by(*self.order_by)
        return qs

    def get_detail_url(self, obj):
        """
        Only relevant on list view.
        :param obj: instance of model to get url for
        Returns: url of
        """
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()
        else:
            raise AttrCrudError('Model instance "{!r}" has no "get_absolute_url" method'.format(obj))

    def gen_short_props(self, obj):
        """
        Generate short property data for a given object.

        :param obj: the object to to find generate attributes for
        :yield: dict of data about each attribute
        """
        for field_info in self._item_info:
            if not field_info.is_long:
                yield self._display_value(obj, field_info)

    def gen_long_props(self, obj):
        """
        Generate long property data for a given object.

        :param obj: the object to to find generate attributes for
        :yield: dict of data about each attribute
        """
        for field_info in self._item_info:
            if field_info.is_long:
                yield self._display_value(obj, field_info)

    @cached_property
    def _item_info(self):
        """
        Returns a list of FieldInfo instances.

        After the first call the list is cached to improve performance.
        :return: list of tuples for each item in display_items
        """
        return list(map(self._getattr_info, self.get_display_items()))

    def get_display_items(self):
        """
        return display items. Override to conditionally alter display items list.
        :return: list of (short) items to display
        """
        return self.display_items

    def _getattr_info(self, attr_name):
        """
        Finds the values for each item returned by _item_info.

        :param attr_name: value direct from display_items
        :return: FieldInfo instance
        """
        field_info = FieldInfo(attr_name)

        if field_info.is_func:
            if field_info.verbose_name is None:
                field_info.verbose_name = self.get_sub_attr(field_info.attr_name) or field_info.attr_name
                field_info.help_text = self.get_sub_attr(field_info.attr_name, 'help_text')
            return field_info

        model, meta, field_names = self.model, self.model._meta, self._field_names
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

    def _display_value(self, obj, field_info):
        """
        Generates a value for an attribute, optionally generate it's url and make it a link and returns it
        together with with it's verbose name.

        If the attribute name refers to a function the value is returned raw (after reversing if rev_view_name,
        otherwise it's processed by convert_to_string.

        :param obj: any instance of the model to get the value from.
        :param field_info: is FieldInfo below
        :return: tuple containing (verbose_name, help_text, value)
        """
        if field_info.is_func:
            value = self.getattr(field_info.attr_name)(obj)
        else:
            value = self._get_object_value(obj, field_info.attr_name)
        url = None
        if field_info.detail_view_link:
            url = self.get_detail_url(obj)
        elif field_info.rev_view_name and hasattr(value, 'pk'):
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
                raise ReverseCrudError('No reverse found for "%s"' % field_info.rev_view_name)

        if field_info.is_func:
            value = self.format_value(value, field_info.field)

        if url:
            value = mark_safe('<a href="%s">%s</a>' % (url, escape(value)))

        return {
            'name': field_info.verbose_name,
            'value': value,
            'help_text': field_info.help_text,
            'extra': self.extra_field_info.get(field_info.attr_name, {})
        }

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
    is_long: boolean indicating if the field should be considered "long"
    """
    field = None
    verbose_name = None
    help_text = None
    rev_view_name = None
    detail_view_link = False
    is_long = False
    is_func = False

    def __init__(self, attr_name):
        self.attr_name = attr_name
        if isinstance(self.attr_name, tuple):
            if len(self.attr_name) == 2:
                self.verbose_name, self.attr_name = self.attr_name
            elif len(self.attr_name) == 3:
                self.verbose_name, self.attr_name, self.help_text = self.attr_name
            else:
                raise SetupCrudError('display_item tuples must be 2 or 3 in length, not %d' % len(self.attr_name))

        if self.attr_name.startswith('long|'):
            self.attr_name = self.attr_name[5:]
            self.is_long = True

        if self.attr_name.startswith('link|'):
            self.attr_name = self.attr_name[5:]
            self.detail_view_link = True

        if self.attr_name.startswith('func|'):
            self.attr_name = self.attr_name[5:]
            self.is_func = True

        if self.attr_name.startswith('rev|'):
            parts = self.attr_name.split('|', 2)
            _, self.rev_view_name, self.attr_name = parts


class GetAttrMixin:
    def getattr(self, name, raise_ex=True):
        if hasattr(self.ctrl, name):
            return getattr(self.ctrl, name)
        return super(GetAttrMixin, self).getattr(name, raise_ex)


class RichListViewMixin(GetAttrMixin, ItemDisplayMixin):
    def get_detail_url(self, obj):
        return self.ctrl.relative_url('details/{}'.format(obj.pk))


class RichDetailViewMixin(GetAttrMixin, ItemDisplayMixin):
    pass


class RichCreateViewMixin(RichViewMixin):
    title = _('Create {verbose_name}')


class RichUpdateViewMixin(RichViewMixin):
    title = _('Update {verbose_name}')


class RichDeleteViewMixin(RichViewMixin):
    title = _('Delete {verbose_name}')
