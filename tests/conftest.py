import os

import django


def pytest_sessionstart():  # type: () -> None
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()
