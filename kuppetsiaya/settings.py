import os
from decouple import config
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "testserver",
]

# Tailwind CSS Configuration
# TAILWIND_CONFIG = {
#     'theme': {
#         'extend': {
#             'colors': {
#                 'primary-green': '#006633',
#                 'secondary-yellow': '#FFCC00',
#             },
#         },
#     },
#     'plugins': [
#         '@tailwindcss/forms',
#         '@tailwindcss/typography',
#     ],
# }

# Path to npm binary
# This might need to be adjusted based on your system setup.
# For example, on Linux it might be '/usr/bin/npm'
# On macOS, it might be '/usr/local/bin/npm'
# If you are using npx, you might need to set this to the path of npx.
# If you are unsure, you can run `which npm` in your terminal to find the path.
# For now, we will assume it is in the PATH. If it fails, this needs to be set explicitly.
import shutil
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
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_email',
    'rest_framework',
    'theme',
    
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
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False

# Session idle timeout (2 minutes = 120 seconds)
SESSION_COOKIE_AGE = 120
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
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
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default=(
        'django.core.mail.backends.smtp.EmailBackend'
        if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
        else 'django.core.mail.backends.console.EmailBackend'
    ),
)
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default=EMAIL_HOST_USER or 'no-reply@kuppetsiaya.or.ke',
)
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
