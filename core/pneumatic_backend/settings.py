# pylint: disable=W,C,R
"""
Django settings for pneumatic_backend project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
import datetime
import os
from os import environ as env
from configurations import Configuration, values
from corsheaders.defaults import default_headers
from pneumatic_backend.webhooks.enums import HookEvent


class Common(Configuration):

    # Internationalization
    # Content-Language response HTTP header
    # contains values from LANGUAGES variable
    # Accept-Language request HTTP determines user locale
    # else used default language from LANGUAGE_CODE variable.
    # Language codes are generally represented in lowercase,
    # but the HTTP Accept-Language header is case-insensitive.
    # The separator is a dash.

    USE_I18N = True  # Enable translation system
    USE_L10N = True  # Enable will display numbers and dates using locale
    LANGUAGE_CODE = env.get('LANGUAGE_CODE', 'en')
    from pneumatic_backend.accounts.enums import Language
    if LANGUAGE_CODE == Language.ru:
        LANGUAGES = Language.CHOICES
    else:
        LANGUAGES = Language.EURO_CHOICES
    TIME_ZONE = 'UTC'
    USE_TZ = True

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    PROJECT_DIR = os.path.dirname(__file__)
    ROOT_URLCONF = 'pneumatic_backend.urls'
    ADMIN_PATH = '__cp'
    LOCALE_PATHS = [
        os.path.join(PROJECT_DIR, os.path.join('accounts', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('analytics', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('authentication', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('generics', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('notifications', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('payment', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('processes', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('services', 'locale')),
        os.path.join(PROJECT_DIR, os.path.join('webhooks', 'locale')),
    ]
    SECRET_KEY = values.SecretValue()
    DEBUG = env.get('DJANGO_DEBUG') == 'yes'
    FRONTEND_URL = env.get('FRONTEND_URL', 'http://localhost')
    EXPIRED_INVITE_PAGE = f'{FRONTEND_URL}/auth/expired-invite'
    PUBLIC_FORMS_ORIGIN = env.get('PUBLIC_FORMS_ORIGIN')

    # Auth
    AUTH_USER_MODEL = 'accounts.User'
    AUTH_TOKEN_ITERATIONS = int(env.get('AUTH_TOKEN_ITERATIONS', 1))

    # Tokens lifetime
    DIGEST_UNSUB_TOKEN_IN_DAYS = 7
    UNSUBSCRIBE_TOKEN_IN_DAYS = 7
    USER_TRANSFER_TOKEN_LIFETIME_IN_DAYS = 7

    ALLOWED_HOSTS = env.get("ALLOWED_HOSTS")
    if ALLOWED_HOSTS:
        ALLOWED_HOSTS = ALLOWED_HOSTS.split(' ')
    else:
        ALLOWED_HOSTS = ['localhost', '0.0.0.0', '127.0.0.1']

    # CORS
    # Sets header:
    # Access-Control-Allow-Origin
    # Access-Control-Allow-Credentials
    # Access-Control-Allow-Headers

    # If CORS_ORIGIN_ALLOW_ALL = True other settings restricting
    # allowed origins will be ignored.
    CORS_ORIGIN_ALLOW_ALL = env.get('CORS_ORIGIN_ALLOW_ALL', 'yes') == 'yes'

    # If CORS_ALLOW_CREDENTIALS = True, cookies will be allowed
    # to be included in cross-site HTTP requests.
    # This sets the Access-Control-Allow-Credentials header
    CORS_ALLOW_CREDENTIALS = env.get('CORS_ALLOW_CREDENTIALS', 'yes') == 'yes'

    # CORS_ALLOW_HEADERS the list of non-standard HTTP headers that you permit
    # in requests from the browser. Sets the Access-Control-Allow-Headers
    # header in responses to preflight requests.
    CORS_ALLOW_HEADERS = list(default_headers) + [
        'X-Guest-Authorization',
        'X-Public-Authorization',
        'Stripe-Signature',
    ]

    # A list of origins that are authorized to make cross-site HTTP requests.
    # A list of origins echoed back to the client in the
    # Access-Control-Allow-Origin header. Defaults to [].
    CORS_ORIGIN_WHITELIST = env.get('CORS_ORIGIN_WHITELIST', None)
    if CORS_ORIGIN_WHITELIST:
        CORS_ORIGIN_WHITELIST = CORS_ORIGIN_WHITELIST.split(' ')
    else:
        CORS_ORIGIN_WHITELIST = []

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'whitenoise.runserver_nostatic',
        'django.contrib.staticfiles',

        'rest_framework',
        'rest_framework_simplejwt',

        'corsheaders',

        'django_extensions',
        'djcelery_email',
        'django_json_widget',
        'django_filters',
        'django_celery_beat',
        'drf_recaptcha',

        'rest_hooks',

        'pneumatic_backend.accounts',
        'pneumatic_backend.authentication',
        'pneumatic_backend.applications',
        'pneumatic_backend.notifications',
        'pneumatic_backend.celery',
        'pneumatic_backend.processes',
        'pneumatic_backend.reports',
        'pneumatic_backend.generics',
        'pneumatic_backend.webhooks',
        'pneumatic_backend.analytics',
        'pneumatic_backend.navigation',
        'pneumatic_backend.pages',
        'pneumatic_backend.faq',
        'tinymce',
        'channels',
        'pneumatic_backend.ai',
        'pneumatic_backend.payment',
        'pneumatic_backend.logs',
    ]

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'pneumatic_backend.authentication.middleware.UserAgentMiddleware',
        'pneumatic_backend.authentication.middleware.AuthMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                os.path.join(BASE_DIR, 'pneumatic_backend/templates/'),
            ],
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

    WSGI_APPLICATION = 'pneumatic_backend.wsgi.application'
    ASGI_APPLICATION = 'pneumatic_backend.asgi.application'
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }

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

    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = (
        'whitenoise.storage.CompressedManifestStaticFilesStorage'
    )

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
        ],
        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated',
        ),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'pneumatic_backend.authentication.services.PublicAuthService',
            'pneumatic_backend.authentication.services.GuestJWTAuthService',
            'pneumatic_backend.authentication.services.'
            'PneumaticTokenAuthentication',
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        'NON_FIELD_ERRORS_KEY': 'errors',
        'TEST_REQUEST_DEFAULT_FORMAT': 'json',
        'DEFAULT_PAGINATION_CLASS': (
            'rest_framework.pagination.LimitOffsetPagination'
        ),

        # Example: 12/min - This means no more 1 request every 5 seconds
        'DEFAULT_THROTTLE_RATES': {
            '01_accounts_invites__token': env.get('THROTTLE_01'),
            '02_processes__create_guest_performer': env.get('THROTTLE_02'),
            '03_processes__template_ai_generation': env.get('THROTTLE_03'),
            '04_services__steps_by_description': env.get('THROTTLE_04'),
            '05_payment__purchase__user': env.get('THROTTLE_05'),
            '06_payment__purchase__api': env.get('THROTTLE_06'),
            '07_auth_ms__token': env.get('THROTTLE_07'),
            '08_auth_ms__auth_uri': env.get('THROTTLE_08'),
            '09_auth0__token': env.get('THROTTLE_09'),
            '10_auth0__auth_uri': env.get('THROTTLE_10'),
            '11_auth__reset_password': env.get('THROTTLE_11'),
        }
    }

    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': datetime.timedelta(hours=6),
        'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=7),
        'AUTH_TOKEN_CLASSES': (
            'rest_framework_simplejwt.tokens.AccessToken',
            'pneumatic_backend.authentication.tokens.GuestToken',
        )
    }

    # Email
    DEFAULT_FROM_EMAIL = env.get(
        'DEFAULT_FROM_EMAIL',
        'Pneumatic <no-reply@pneumatic.app>'
    )
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_DATE_FORMAT = '%a, %d %b %Y %I:%M:%S %p UTC'

    # Customer.io
    CUSTOMERIO_WEBHOOK_API_VERSION = env.get('CIO_WEBHOOK_API_VERSION')
    CUSTOMERIO_WEBHOOK_API_KEY = env.get('CIO_WEBHOOK_API_KEY')
    CUSTOMERIO_TRANSACTIONAL_API_KEY = env.get('CIO_TRANSACTIONAL_API_KEY')

    # Environments
    CONFIGURATION_DEV = 'Development'
    CONFIGURATION_TESTING = 'Testing'
    CONFIGURATION_STAGING = 'Staging'
    CONFIGURATION_PROD = 'Production'
    CONFIGURATION_CURRENT = env.get(
        'ENVIRONMENT', CONFIGURATION_DEV
    ).title()

    # Stripe
    STRIPE_SECRET_KEY = env.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = env.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_WEBHOOK_IP_WHITELIST = env.get('STRIPE_WEBHOOK_IP_WHITELIST', [])
    if STRIPE_WEBHOOK_IP_WHITELIST:
        STRIPE_WEBHOOK_IP_WHITELIST = STRIPE_WEBHOOK_IP_WHITELIST.split(' ')
    else:
        STRIPE_WEBHOOK_IP_WHITELIST = []

    # Pay Wall
    PAYWALL_MAX_ACTIVE_TEMPLATES = 5
    PAYWALL_MIN_USERS = 1
    FREEMIUM_MAX_USERS = 5

    # Account verification
    VERIFICATION_CHECK = env.get('VERIFICATION_CHECK') == 'yes'
    VERIFICATION_DEADLINE_IN_DAYS = 7
    MAX_INVITES = 5

    # Private API
    PRIVATE_API_CHECK_IP = env.get('PRIVATE_API_CHECK_IP') == 'yes'
    PRIVATE_API_IP_WHITELIST = env.get('PRIVATE_API_IP_WHITELIST')
    if PRIVATE_API_IP_WHITELIST:
        PRIVATE_API_IP_WHITELIST = PRIVATE_API_IP_WHITELIST.split(' ')

    # Google Cloud
    GCLOUD_BUCKET_NAME = env.get('GCLOUD_BUCKET_NAME')

    # Slack
    SLACK = env.get('SLACK') == 'yes'
    SLACK_CONFIG = {
        'NOTIFY_ON_SIGNUP': env.get('SLACK_NOTIFY_ON_SIGNUP') == 'yes',
        'SIGNUP_CHANNEL': env.get('SLACK_SIGNUP_CHANNEL'),
        'DIGEST_CHANNEL': env.get('SLACK_DIGEST_CHANNEL'),
        'MARVIN_TOKEN': env.get('SLACK_MARVIN_TOKEN'),
    }

    # Segment
    ANALYTICS_WRITE_KEY = env.get('ANALYTICS_WRITE_KEY')
    ANALYTICS_DEBUG = env.get('ANALYTICS_DEBUG') == 'yes'

    # WebHooks
    HOOK_CUSTOM_MODEL = 'webhooks.models.WebHook'
    HOOK_FINDER = 'pneumatic_backend.webhooks.utils.find_and_fire_hook'
    HOOK_EVENTS = {
        HookEvent.WORKFLOW_COMPLETED: None,
        HookEvent.WORKFLOW_STARTED: None,
        HookEvent.TASK_STARTED: None,
        HookEvent.TASK_RETURNED: None
    }

    # Attachments
    ATTACHMENT_SIGNED_URL_LIFETIME_MIN = 15
    ATTACHMENT_MAX_SIZE_BYTES = 104857600  # bites = 100 Mb

    # Notifications
    NOTIFICATIONS_NOT_READ_TIMEOUT = datetime.timedelta(minutes=1)

    # Celery
    CELERY_BROKER_URL = env.get('CELERY_BROKER_URL')
    CELERY_IMPORTS = [
        'pneumatic_backend.accounts.tasks',
        'pneumatic_backend.authentication.tasks',
        'pneumatic_backend.processes.tasks.delay',
        'pneumatic_backend.processes.tasks.digest',
        'pneumatic_backend.processes.tasks.tasks',
        'pneumatic_backend.processes.tasks.update_workflow',
        'pneumatic_backend.processes.tasks.webhooks',
        'pneumatic_backend.webhooks.tasks',
        'pneumatic_backend.services.tasks',
    ]

    # reCaptcha
    DRF_RECAPTCHA_SITE_KEY = env.get('RECAPTCHA_SITE_KEY', 'key')
    DRF_RECAPTCHA_SECRET_KEY = env.get('RECAPTCHA_SECRET_KEY', 'key')
    DRF_RECAPTCHA_TESTING = env.get('RECAPTCHA_TESTING', 'yes') == 'yes'

    # Firebase Credentials
    FIREBASE_PUSH_APPLICATION_CREDENTIALS = env.get(
        'FIREBASE_PUSH_APPLICATION_CREDENTIALS'
    )

    # OpenAI
    OPENAI_API_KEY = env.get('OPENAI_API_KEY')
    OPENAI_API_ORG = env.get('OPENAI_API_ORG')

    # Microsoft auth
    MS_CLIENT_ID = env.get('MS_CLIENT_ID')
    MS_CLIENT_SECRET = env.get('MS_CLIENT_SECRET')
    MS_AUTHORITY = env.get('MS_AUTHORITY')

    # SSO Auth0
    AUTH0_CLIENT_ID = env.get('AUTH0_CLIENT_ID')
    AUTH0_CLIENT_SECRET = env.get('AUTH0_CLIENT_SECRET')
    AUTH0_DOMAIN = env.get('AUTH0_DOMAIN')
    AUTH0_REDIRECT_URI = env.get('AUTH0_REDIRECT_URI')

    REPLICA = 'replica'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env.get('POSTGRES_DB', 'pneumatic'),
            'USER': env.get('POSTGRES_USER', 'pneumatic'),
            'PASSWORD': env.get('POSTGRES_PASSWORD', 'pneumatic'),
            'HOST': env.get('POSTGRES_HOST', 'localhost'),
            'PORT': env.get('POSTGRES_PORT', '5432'),
        }
    }

    # False value to disable some features.
    PROJECT_CONF = {
        'CAPTCHA': env.get('CAPTCHA') == 'yes',
        'ANALYTICS': env.get('ANALYTICS') == 'yes',
        'BILLING': env.get('BILLING') == 'yes',
        'SIGNUP': env.get('SIGNUP') == 'yes',
        'MS_AUTH': env.get('MS_AUTH') == 'yes',
        'GOOGLE_AUTH': env.get('GOOGLE_AUTH') == 'yes',
        'SSO_AUTH': env.get('SSO_AUTH') == 'yes',
        'EMAIL': env.get('EMAIL') == 'yes',
        'EMAIL_PROVIDER': env.get('EMAIL_PROVIDER'),
        'AI': env.get('AI') == 'yes',
        'AI_PROVIDER': env.get('AI_PROVIDER'),
        'PUSH': env.get('PUSH') == 'yes',
        'PUSH_PROVIDER': env.get('PUSH_PROVIDER'),
        'STORAGE': env.get('STORAGE') == 'yes',
        'STORAGE_PROVIDER': env.get('STORAGE_PROVIDER'),
        'SENTRY_DSN': env.get('SENTRY_DSN'),
    }


class Development(Common):

    INSTALLED_APPS = Common.INSTALLED_APPS + ['pylint_django']
    TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

    # CELERY_ALWAYS_EAGER mean that Celery will not schedule tasks
    # to run as it would regularly do, via sending a message to the broker.
    # Instead, it will run it inside the process that is calling the task
    # (via .apply_async() or .delay()).
    CELERY_ALWAYS_EAGER = True

    # If CELERY_EAGER_PROPAGATES_EXCEPTIONS is True,
    # eagerly executed tasks (applied by task.apply(),
    # or when the CELERY_ALWAYS_EAGER setting is enabled),
    # will propagate exceptions.
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

    # Default: 'django.contrib.sessions.backends.db'
    # Controls where Django stores session data.
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

    # SESSION_CACHE_ALIAS mean that if you have multiple caches
    # defined in CACHES, Django will use the default cache.
    # To use another cache set SESSION_CACHE_ALIAS to the name of that cache.
    SESSION_CACHE_ALIAS = 'session'

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'default',
        },
        'auth': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'auth',
        },
        'session': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'session',
        }
    }


class Testing(Development):

    pass


class Staging(Common):

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env.get('POSTGRES_DB', 'pneumatic'),
            'USER': env.get('POSTGRES_USER', 'pneumatic'),
            'PASSWORD': env.get('POSTGRES_PASSWORD', 'pneumatic'),
            'HOST': env.get('POSTGRES_HOST', 'localhost'),
            'PORT': env.get('POSTGRES_PORT', '5432'),
        },
        'replica': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env.get('POSTGRES_REPLICA_DB', 'pneumatic'),
            'USER': env.get('POSTGRES_REPLICA_USER', 'pneumatic'),
            'PASSWORD': env.get('POSTGRES_REPLICA_PASSWORD', 'pneumatic'),
            'HOST': env.get('POSTGRES_REPLICA_HOST', 'localhost'),
            'PORT': env.get('POSTGRES_REPLICA_PORT', '5432')
        }
    }

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env.get('CACHE_REDIS_URL', ''),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "retry_on_timeout": True,
                    "health_check_interval": 30,
                }
            },
            "KEY_PREFIX": "default",
        },
        'auth': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env.get('AUTH_REDIS_URL', ''),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                "CONNECTION_POOL_KWARGS": {
                    "retry_on_timeout": True,
                    "health_check_interval": 30,
                }
            },
            'KEY_PREFIX': '',
        },
        'session': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env.get('SESSION_REDIS_URL', ''),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                "CONNECTION_POOL_KWARGS": {
                    "retry_on_timeout": True,
                    "health_check_interval": 30,
                }
            },
            'KEY_PREFIX': '',
        },
    }

    # WebHooks
    HOOK_DELIVERER = 'pneumatic_backend.webhooks.tasks.deliver_hook_wrapper'

    # Channels
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [env.get('CHANNELS_REDIS_URL', '')]
            }
        }
    }

    MAX_INVITES = 10


class Production(Staging):

    MAX_INVITES = 100
    NOTIFICATIONS_NOT_READ_TIMEOUT = datetime.timedelta(hours=3)
