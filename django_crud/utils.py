from django.core.urlresolvers import reverse as _reverse


def reverse(viewname, *args, **kwargs):
    return _reverse(viewname, args=args, kwargs=kwargs)
