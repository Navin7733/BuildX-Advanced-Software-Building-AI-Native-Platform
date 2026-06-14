"""
BuildX Django Settings — Base
"""
import os
from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = env('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ─── Applications ────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    # BuildX apps
    'apps.accounts',
    'apps.projects',
    'apps.agents',
    'apps.memory',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'buildx.urls'
WSGI_APPLICATION = 'buildx.wsgi.application'
ASGI_APPLICATION = 'buildx.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

# ─── Database (MongoDB via pymongo — no ORM) ─────────────────
# MongoDB is accessed directly via pymongo in db.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # Only for Django internals (sessions, etc.)
    }
}

MONGODB_URI = env('MONGODB_URI', default='mongodb://localhost:27017/buildx')
MONGODB_DB_NAME = env('MONGODB_DB_NAME', default='buildx')

# ─── Redis / Channels / Celery ────────────────────────────────
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per agent task

# Celery queues per agent type
CELERY_TASK_QUEUES = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'planner': {'exchange': 'agents', 'routing_key': 'planner'},
    'architect': {'exchange': 'agents', 'routing_key': 'architect'},
    'frontend': {'exchange': 'agents', 'routing_key': 'frontend'},
    'backend_dev': {'exchange': 'agents', 'routing_key': 'backend_dev'},
    'reviewer': {'exchange': 'agents', 'routing_key': 'reviewer'},
    'testing': {'exchange': 'agents', 'routing_key': 'testing'},
    'documentation': {'exchange': 'agents', 'routing_key': 'documentation'},
    'deployment': {'exchange': 'agents', 'routing_key': 'deployment'},
    'memory': {'exchange': 'agents', 'routing_key': 'memory'},
}

# ─── REST Framework ───────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ─── JWT ─────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ─── CORS ─────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://localhost:5173',
])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization',
    'content-type', 'dnt', 'origin', 'user-agent',
    'x-csrftoken', 'x-requested-with',
]

# ─── LLM / OpenRouter ─────────────────────────────────────────
OPENROUTER_API_KEY = env('OPENROUTER_API_KEY', default='')
OPENROUTER_BASE_URL = env('OPENROUTER_BASE_URL', default='https://openrouter.ai/api/v1')
LLM_DEFAULT_MODEL = env('LLM_DEFAULT_MODEL', default='openai/gpt-4o-mini')
LLM_PREMIUM_MODEL = env('LLM_PREMIUM_MODEL', default='anthropic/claude-3.5-sonnet')
LLM_FAST_MODEL = env('LLM_FAST_MODEL', default='meta-llama/llama-3.1-8b-instruct:free')

# ─── Embeddings ────────────────────────────────────────────────
# OpenRouter does NOT support the /embeddings endpoint.
# Use a real OpenAI key for cloud embeddings, or set EMBEDDING_PROVIDER=local
# to use the bundled sentence-transformers model (no API key required).
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
EMBEDDING_MODEL = env('EMBEDDING_MODEL', default='text-embedding-3-small')
EMBEDDING_PROVIDER = env('EMBEDDING_PROVIDER', default='local')  # 'local' | 'openai'

# ─── MCP ──────────────────────────────────────────────────────
MCP_FILESYSTEM_ROOT = env('MCP_FILESYSTEM_ROOT', default='/projects')
MCP_GITHUB_TOKEN = env('MCP_GITHUB_TOKEN', default='')

# ─── Static & Media ──────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = True

# ─── Logging ─────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'buildx': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'celery': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
