from django.conf import settings

from .exceptions import SetupCrudError

if not hasattr(settings, 'BASE_TEMPLATE'):
    raise SetupCrudError('"BASE_TEMPLATE" must be defined in settings')
