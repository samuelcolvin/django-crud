import pytest

import os


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unit_tests.settings')
    import django
    django.setup()


@pytest.fixture(scope='session')
def db_setup():
    from django.core.management import call_command
    call_command('migrate')


@pytest.yield_fixture
def db(db_setup):
    from django.db import transaction
    sid = transaction.savepoint()
    yield None
    transaction.savepoint_rollback(sid)
