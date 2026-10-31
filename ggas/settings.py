import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .rest_framework_settings import *  # noqa: F403
from .spectacular_settings import *  # noqa: F403

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'ggas-dev-apenas-local-nao-usar-fora-desta-maquina',
)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [
    host for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host
]

CORS_ALLOW_CREDENTIALS = True

cors_origins = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,https://localhost:3000,https://127.0.0.1:3000',
)
CORS_ALLOWED_ORIGINS = [origin for origin in cors_origins.split(',') if origin]

DJANGO_DB_KEY = os.environ.get('DJANGO_DB_KEY', '')
if not DJANGO_DB_KEY and 'test' in sys.argv:
    DJANGO_DB_KEY = 'chave-somente-dos-testes-automatizados'

DATABASES = {
    'default': {
        'ENGINE': 'ggas.db.sqlite_cifrado',
        'NAME': BASE_DIR / 'db.sqlite3',
        'PASSWORD': DJANGO_DB_KEY,
    }
}

SESSAO_COOKIE_NAME = 'ggas_sessao'
SESSAO_COOKIE_AGE = 60 * 60 * 8
SESSAO_COOKIE_SECURE = os.environ.get('DJANGO_COOKIE_SECURE', 'True' if not DEBUG else 'False') == 'True'
if 'test' in sys.argv:
    SESSAO_COOKIE_SECURE = False

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SSL_REDIRECT', 'False') == 'True'

AUTH_USER_MODEL = 'colaboradores.User'

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DEFAULT_ROOT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'simple_history',
]

AUTH_APPS = [
    'Auth.auth',
]

COLABORADORES_APPS = [
    'Colaboradores.colaboradores',
]

CLIENTES_APPS = [
    'Clientes.clientes',
]

CATALOGO_APPS = [
    'Catalogo.produtos',
    'Catalogo.fornecedores',
]

AUDITORIA_APPS = [
    'Auditoria.auditoria',
]

ESTOQUE_APPS = [
    'Estoque.estoque',
]

PEDIDOS_APPS = [
    'Pedidos.pedidos',
]

RELATORIOS_APPS = [
    'Relatorios.relatorios',
]

INSTALLED_APPS = (
    DEFAULT_ROOT_APPS
    + AUTH_APPS
    + COLABORADORES_APPS
    + CLIENTES_APPS
    + CATALOGO_APPS
    + AUDITORIA_APPS
    + ESTOQUE_APPS
    + PEDIDOS_APPS
    + RELATORIOS_APPS
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'ggas.urls'
WSGI_APPLICATION = 'ggas.wsgi.application'
ASGI_APPLICATION = 'ggas.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
