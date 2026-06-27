import shutil
import dj_database_url
import logging
import sys
from pathlib import Path
from decouple import config

logger = logging.getLogger(__name__)


def str_to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    return bool(value and value.lower() in ('true', '1', 'yes', 'on')) if value else default


def csv_config(name, default=''):
    return [item.strip() for item in config(name, default=default).split(',') if item.strip()]


def unique_list(values):
    seen = set()
    return [x for x in values if x and x not in seen and not seen.add(x)]


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = str_to_bool(config('DEBUG', default='False'))

RAILWAY_PUBLIC_DOMAIN = config('RAILWAY_PUBLIC_DOMAIN', default='').strip()

ALLOWED_HOSTS = unique_list([
    "127.0.0.1", "localhost", "0.0.0.0", "testserver",
    "albert-incult-superfluously.ngrok-free.dev", ".railway.app", RAILWAY_PUBLIC_DOMAIN,
] + csv_config('ALLOWED_HOSTS'))

NPM_BIN_PATH = shutil.which('npm')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'theme',
    'rest_framework',
    
    # Project apps
    'core',
    'accounts',
    'news',
    'gallery',
    'projects',
    'dashboard',
    'financials',
    'bbf',
    'support',
]

# TAILWIND_APP_NAME = 'theme'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# WhiteNoise for static file serving in production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Static files storage - use simple storage for development
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'kuppetsiaya.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.bbf_contacts',
            ],
        },
    },
]

WSGI_APPLICATION = 'kuppetsiaya.wsgi.application'


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'kuppet',
#         'USER': 'kuppet',
#         'PASSWORD': '11C4pt41n254.',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# DATABASE_ROUTERS = ['kuppetsiaya.routers.LegacyRouter']

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
CSRF_TRUSTED_ORIGINS = unique_list([
    'https://albert-incult-superfluously.ngrok-free.dev',
    'http://127.0.0.1:8010', 'http://localhost:8010',
] + ([f'https://{RAILWAY_PUBLIC_DOMAIN}'] if RAILWAY_PUBLIC_DOMAIN else []) + csv_config('CSRF_TRUSTED_ORIGINS'))

# Railway terminates SSL at the load balancer; trust X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# OTP expiry is enforced inside the OTP challenge; keep the signed-in session usable.
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=1209600, cast=int)
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.CustomUser'

# ASGI application for concurrent request handling
ASGI_APPLICATION = 'kuppetsiaya.asgi.application'

# Database-specific connection options
db_engine = DATABASES['default']['ENGINE']
DATABASES['default'].setdefault('OPTIONS', {})

if db_engine == 'django.db.backends.sqlite3':
    DATABASES['default']['OPTIONS']['timeout'] = 30
elif db_engine == 'django.db.backends.postgresql':
    DATABASES['default']['OPTIONS']['connect_timeout'] = 10

# Increase max connections for concurrent requests
CONN_MAX_AGE = 60

# Email / SMTP settings
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = str_to_bool(config('EMAIL_USE_TLS', default='True'))
EMAIL_USE_SSL = str_to_bool(config('EMAIL_USE_SSL', default='False'))
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)

RESEND_API_KEY = config('RESEND_API_KEY', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@kuppetsiaya.or.ke')

EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default=(
        'django_resend.backends.ResendBackend'
        if RESEND_API_KEY
        else 'django.core.mail.backends.smtp.EmailBackend'
        if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
        else 'django.core.mail.backends.console.EmailBackend'
    ),
)
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}:{lineno} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'verbose' if DEBUG else 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    },
}

try:
    import sentry_sdk
    if not DEBUG and config('SENTRY_DSN', default=''):
        sentry_sdk.init(dsn=config('SENTRY_DSN'), traces_sample_rate=0.1)
except ImportError:
    pass
