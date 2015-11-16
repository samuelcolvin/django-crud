SECRET_KEY = 'testing'
DEBUG = True

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django_jinja',
    'bootstrapform_jinja',
    'django_crud',
    'tests',
)

# MIDDLEWARE_CLASSES = (
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.security.SecurityMiddleware',
# )

ROOT_URLCONF = 'tests.settings'
urlpatterns = []

context_processors = (
    # 'django.template.context_processors.debug',
    # 'django.template.context_processors.request',
    # 'django.contrib.auth.context_processors.auth',
    # 'django.contrib.messages.context_processors.messages',
    'django_crud.context.crud_context',
)

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'APP_DIRS': True,
        'OPTIONS': {
            'match_extension': '.jinja',
            'trim_blocks': True,
            'lstrip_blocks': True,
            'context_processors': context_processors
        },
    }
]

BASE_TEMPLATE = 'base.jinja'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
STATIC_URL = '/static/'
