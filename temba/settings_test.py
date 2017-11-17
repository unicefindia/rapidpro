from __future__ import absolute_import, unicode_literals

# -----------------------------------------------------------------------------------
# Sample RapidPro settings file, this should allow you to deploy RapidPro locally on
# a PostgreSQL database.
#
# The following are requirements:
#     - a postgreSQL database named 'temba', with a user name 'temba' and
#       password 'temba' (with postgis extensions installed)
#     - a redis instance listening on localhost
# -----------------------------------------------------------------------------------

import warnings
import copy

from .settings_common import *  # noqa

DEBUG_TOOLBAR = False

# -----------------------------------------------------------------------------------
# Used when creating callbacks for Twilio, Nexmo etc..
# -----------------------------------------------------------------------------------
HOSTNAME = 'temba.ngrok.io'
TEMBA_HOST = 'temba.ngrok.io'
ALLOWED_HOSTS = ['localhost', 'temba.ngrok.io']

# -----------------------------------------------------------------------------------
# Redis & Cache Configuration (we expect a Redis instance on localhost)
# -----------------------------------------------------------------------------------
REDIS_DB = 2
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://%s:%s/%s" % (REDIS_HOST, REDIS_PORT, REDIS_DB),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

BROKER_URL = CACHES['default']['LOCATION']

ANONYMOUS_USER_NAME = 'AnonymousUser'

# -----------------------------------------------------------------------------------
# Need a PostgreSQL database on localhost with postgis extension installed.
# -----------------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'rapidpro_master_quick',
        'USER': 'postgres',
        'PASSWORD': 't.amaral',
        'HOST': 'localhost',
        'PORT': '',
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 60,
        'OPTIONS': {}
    },
    'default2': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'rapidpro_master_quick',
        'USER': 'postgres',
        'PASSWORD': 't.amaral',
        'HOST': 'localhost',
        'PORT': '',
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 60,
        'OPTIONS': {}
    }
}

INTERNAL_IPS = ('127.0.0.1',)

# -----------------------------------------------------------------------------------
# Add a custom brand for development
# -----------------------------------------------------------------------------------

custom = copy.deepcopy(BRANDING['rapidpro.io'])
custom['name'] = 'Custom Brand'
custom['slug'] = 'custom'
custom['org'] = 'Custom'
custom['api_link'] = 'http://custom-brand.io'
custom['domain'] = 'custom-brand.io'
custom['email'] = 'join@custom-brand.io'
custom['support_email'] = 'support@custom-brand.io'
custom['allow_signups'] = True
BRANDING['custom-brand.io'] = custom

# -----------------------------------------------------------------------------------
# Load development apps
# -----------------------------------------------------------------------------------
INSTALLED_APPS = INSTALLED_APPS + ('storages',)
if DEBUG_TOOLBAR:
    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar', )

# -----------------------------------------------------------------------------------
# In development, add in extra logging for exceptions and the debug toolbar
# -----------------------------------------------------------------------------------
MIDDLEWARE_CLASSES = ('temba.middleware.ExceptionMiddleware',) + MIDDLEWARE_CLASSES
if DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE_CLASSES

# -----------------------------------------------------------------------------------
# In development, perform background tasks in the web thread (synchronously)
# -----------------------------------------------------------------------------------
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_BACKEND = 'memory'

# -----------------------------------------------------------------------------------
# This setting throws an exception if a naive datetime is used anywhere. (they should
# always contain a timezone)
# -----------------------------------------------------------------------------------
warnings.filterwarnings('error', r"DateTimeField .* received a naive datetime",
                        RuntimeWarning, r'django\.db\.models\.fields')

# -----------------------------------------------------------------------------------
# Make our sitestatic URL be our static URL on development
# -----------------------------------------------------------------------------------
STATIC_URL = '/sitestatic/'
