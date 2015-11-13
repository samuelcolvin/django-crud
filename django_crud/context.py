from django.conf import settings


def crud_context(request):
    return {
        'base_template': settings.BASE_TEMPLATE
    }
