from django.conf import settings


def crud_context(request):
    return {
        'base_template': settings.BASE_TEMPLATE,
        'include_crud_assets': getattr(settings, 'INCLUDE_CRUD_ASSETS', True)
    }
