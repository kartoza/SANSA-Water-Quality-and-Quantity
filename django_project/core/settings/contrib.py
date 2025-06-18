# coding=utf-8
"""Settings for 3rd party."""
from .base import *  # noqa

# Extra installed apps
INSTALLED_APPS = INSTALLED_APPS + (
    'corsheaders',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework.authtoken',
    'guardian',
    'django_cleanup.apps.CleanupConfig',
    'django_celery_beat',
    'django_celery_results',
    'leaflet',
    'constance',
    'constance.backends.database',
)
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS':
    'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated', ),
    'DEFAULT_VERSIONING_CLASS': ('rest_framework.versioning.NamespaceVersioning'),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'guardian.backends.ObjectPermissionBackend',
)
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
CELERY_RESULT_BACKEND = 'django-db'

TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'django.template.context_processors.request',
]

SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_CONFIG = {
    'AWEI_THRESHOLD': (-0.11, 'AWEI threshold value for detecting water body', float),
    'WATER_BODY_MIN_PIXEL': (100, 'Minimum pixels to consider as water body', int),
    'MOSAIC_MAX_THREADS': (4, 'Maximum threads for genrating mosaic', int),
    'MOSAIC_BATCH_SIZE': (500, 'Batch size number for generating mosaic', int),
    'MOSAIC_TARGET_CRS': ('EPSG:6933', 'Target CRS of the mosaic', str),
}


# Allow your React frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
]
CORS_ALLOW_CREDENTIALS = True
