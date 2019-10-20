SECRET_KEY = "strong enough for a woman, made for a man"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "multi",
        "USER": "multi",
        "PASSWORD": "multi",
        "HOST": "::1",
        "PORT": 5432,
    }
}
INSTALLED_APPS = ["django.contrib.contenttypes", "tests.testapp"]
