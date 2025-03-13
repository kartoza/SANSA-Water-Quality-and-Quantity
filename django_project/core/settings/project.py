# coding=utf-8

"""Project level settings.

Adjust these values as needed but don't commit passwords etc. to any public
repository!
"""
import os  # noqa
from celery.schedules import crontab

from .contrib import *  # noqa

ALLOWED_HOSTS = ['*']
ADMINS = (
    ('Dimas Ciputra', 'dimas@kartoza.com'),
)
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ['DATABASE_NAME'],
        'USER': os.environ['DATABASE_USERNAME'],
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': 5432,
        'TEST_NAME': 'unittests',
    }
}

# Set debug to false for production
DEBUG = TEMPLATE_DEBUG = False

# Extra installed apps
INSTALLED_APPS = INSTALLED_APPS + (
    'core',
    'project'
)

# Celery Beat
CELERY_BEAT_SCHEDULE = {
    'update_stored_data_monthly': {
        'task': 'update_stored_data',
        'schedule': crontab(minute='0', hour='0', day_of_week='*', day_of_month='1', month_of_year='*')
    }
}