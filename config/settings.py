import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1").split(",")

ROOT_URLCONF = 'config.urls'  # remplace 'config' par le nom de ton dossier principal contenant urls.py


# Database
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}



INSTALLED_APPS = [
    'django.contrib.admin',        # <- nécessaire pour /admin
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Ajoute ici tes apps propres comme 'core', etc.
    'core',
    'django.contrib.humanize'
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # ✅ AVANT
    'core.middleware.TenantMiddleware',   # <-- added tenant middleware (position can be adjusted)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # pour tes templates custom
        'APP_DIRS': True,                  # indispensable pour admin
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',   # obligatoire pour admin
                'django.contrib.auth.context_processors.auth',  # obligatoire pour admin
                'django.contrib.messages.context_processors.messages',  # obligatoire pour admin
            ],
        },
    },
]

# Après INSTALLED_APPS
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Messages framework (si pas déjà présent)
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_TENANT_NAME = os.getenv("DEFAULT_TENANT_NAME", "default")
DEFAULT_TENANT_DOMAIN = os.getenv("DEFAULT_TENANT_DOMAIN", "default")
AUTH_USER_MODEL = 'core.User'


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'