"""
Modified django-jinja backend which provides access to context in http responses.
"""

import sys

from django_jinja.backend import Jinja2, Template
import jinja2

from django.template import TemplateDoesNotExist
from django.template import TemplateSyntaxError
from django.middleware.csrf import get_token
from django.utils.encoding import smart_text
from django.utils.functional import SimpleLazyObject
from django.utils import six
from .conftest import current_response


class TemplateWithContext(Template):
    def render(self, context=None, request=None):
        if request is not None:
            def _get_val():
                token = get_token(request)
                if token is None:
                    return 'NOTPROVIDED'
                else:
                    return smart_text(token)

            context["request"] = request
            context["csrf_token"] = SimpleLazyObject(_get_val)

            # Support for django context processors
            for processor in self.backend.context_processors:
                context.update(processor(request))

        current_response.set(context)
        return self.template.render(context)


class Jinja2WithContext(Jinja2):
    def get_template(self, template_name):
        if not self.match_template(template_name):
            raise TemplateDoesNotExist("Template {} does not exists".format(template_name))

        try:
            return TemplateWithContext(self.env.get_template(template_name), self)
        except jinja2.TemplateNotFound as exc:
            six.reraise(TemplateDoesNotExist, TemplateDoesNotExist(exc.args), sys.exc_info()[2])
        except jinja2.TemplateSyntaxError as exc:
            six.reraise(TemplateSyntaxError, TemplateSyntaxError(exc.args), sys.exc_info()[2])
