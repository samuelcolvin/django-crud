import os
import pytest

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
    from django.db import transaction
    with transaction.atomic():
        yield None
        transaction.set_rollback(True)


@pytest.fixture
def request():
    def request_factory(url='/'):
        return RequestFactory().get(url)
    return request_factory
