from mysite.common_settings import *

SECRET_KEY = "aje#lg$7!t!tc5*i%ittn(to%5#5%vjvi*oc=ib25wx%+##_b+"

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "game_corpus_db",
        "HOST": "127.0.0.1",
        "USER": "tmahrt",
        "PASSWORD": "12345678",
    }
}