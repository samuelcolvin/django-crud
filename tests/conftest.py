import os
import pytest

from django.db import transaction
from django.test import RequestFactory


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    import django
    django.setup()


@pytest.fixture(scope='session')
def db_setup():
    from django.core.management import call_command
    call_command('migrate')


@pytest.yield_fixture
def db(db_setup):
    with transaction.atomic():
        yield None
        transaction.set_rollback(True)


class CurrentResponse:
    # TODO this could be done much more elegantly
    _ctx = None

    def set(self, ctx):
        self._ctx = ctx and dict(ctx)

    @property
    def context(self):
        return self._ctx

current_response = CurrentResponse()


class SimpleRequestFactory(RequestFactory):
    def __call__(self, url='/'):
        return self.get(url)


@pytest.yield_fixture
def http_request():
    yield SimpleRequestFactory()
    current_response.set(None)
