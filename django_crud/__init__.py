"""
django-crud
-----------

CRUD controllers for django: Create, Retrieve, Update, Delete, List

:copyright: (c) 2015 by Samuel Colvin
:license: MIT. See LICENSE for more details
"""
from django.core.checks import Error, register

__title__ = 'django_crud'
__version__ = '0.1.0'
__author__ = 'Samuel Colvin'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Samuel Colvin'


@register()
def example_check(app_configs, **kwargs):
    from django.conf import settings
    errors = []
    if not hasattr(settings, 'BASE_TEMPLATE'):  # pragma: no cover
        errors.append(
            Error(
                '"BASE_TEMPLATE" not defined',
                hint='define BASE_TEMPLATE in settings.py',
                obj='django_crud',
                id='django_crud.E001',
            )
        )
    return errors
