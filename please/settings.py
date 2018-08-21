"""
Django settings for please project.

Generated by 'django-admin startproject' using Django 1.8.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$5-8y535aj3+^jrgpnkf1d5@9x7=dem8!me*s)8h^+1o4ex2d5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')

# Application definition

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, 6379)],
        },
        "ROUTING": "please.routing.channel_routing",
    },
}

INSTALLED_APPS = (
    'monitor',
    'web',
    'chat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'simple_history',
    'constance',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'please.urls'
MEDIA_ROOT = 'web/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'please.wsgi.application'


# Email

EMAIL_HOST = 'smtpout.secureserver.net'
EMAIL_HOST_USER = 'contato@redeplis.org'
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'contato@redeplis.org'
SERVER_EMAIL = 'contato@redeplis.org'
EMAIL_PORT = 80
EMAIL_USE_TLS = False


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'please_prod',
        'USER': 'please',
        'PASSWORD': 'please',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LOGIN_URL = '/user/login'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'


#CONSTANCE
CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True

CONSTANCE_CONFIG = {
    'TWITTER_CONSUMER_KEY': ('', 'Twitter consumer key', str),
    'TWITTER_CONSUMER_SECRET': ('', 'Twitter consumer secret', str),
    'TWITTER_ACCESS_TOKEN_KEY': ('', 'Twitter access token key', str),
    'TWITTER_ACCESS_TOKEN_SECRET': ('', 'Twitter access token secret', str),
    'TWITTER_OWNER_ID': ('', 'Twitter owner/account id', str),
    'PLEASE_TREATMENT_IS_ACTIVE': (False, 'Treatment is active', bool),
    'PLEASE_INVITE_MESSAGE': ('', 'Mensagem automática de convite', str),
    'PLEASE_TREATMENT_INACTIVE_MESSAGE': ('', 'Resposta automática de atendimento indisponível', str),
    'PLEASE_TREATMENT_WAITING_MESSAGE': ('', 'Resposta automática de espera para atendimento', str),
    'PLEASE_TREATMENT_CLODED_MESSAGE': ('', 'Mensagem automática de atendimento finalizado', str),
    'PLEASE_TREATMENT_ACTIVE_TWEET_MESSAGE': ('', 'Mensagem de Tweet para atendimento aberto', str),
    'PLEASE_TREATMENT_INACTIVE_TWEET_MESSAGE': ('', 'Mensagem de Tweet para atendimento fechado', str),
}


CONSTANCE_CONFIG_FIELDSETS = {
    'Twitter App': ('TWITTER_CONSUMER_KEY', 'TWITTER_CONSUMER_SECRET', \
                    'TWITTER_ACCESS_TOKEN_KEY', 'TWITTER_ACCESS_TOKEN_SECRET', \
                    'TWITTER_OWNER_ID'),
    'General': ('PLEASE_TREATMENT_IS_ACTIVE', 'PLEASE_INVITE_MESSAGE', \
                'PLEASE_TREATMENT_INACTIVE_MESSAGE', 'PLEASE_TREATMENT_WAITING_MESSAGE',
                'PLEASE_TREATMENT_CLODED_MESSAGE',
                'PLEASE_TREATMENT_ACTIVE_TWEET_MESSAGE',
                'PLEASE_TREATMENT_INACTIVE_TWEET_MESSAGE'),
}
