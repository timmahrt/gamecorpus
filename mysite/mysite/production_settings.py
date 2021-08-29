from mysite.common_settings import *


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ""

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "game_corpus_db",
        "HOST": "127.0.0.1",
        "USER": "",
        "PASSWORD": "",
    }
}
