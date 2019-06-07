# vim: set fileencoding=utf-8
"""
Django settings for myhelpline project.

Generated by 'django-admin startproject' using Django 1.8.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import logging
import os
import socket
import subprocess  # noqa, used by included files
import sys
from imp import reload

from future.moves.urllib.parse import urljoin

from past.builtins import basestring

from django.core.exceptions import SuspiciousOperation
from django.utils.log import AdminEmailHandler

from celery.signals import after_setup_logger

# setting default encoding to utf-8
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding("utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = BASE_DIR

PRINT_EXCEPTION = False


TEMPLATED_EMAIL_TEMPLATE_DIR = 'templated_email/'
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'noreply@helpline.co.ke'
SHARE_PROJECT_SUBJECT = '{} Project has been shared with you.'
SHARE_ORG_SUBJECT = '{}, You have been added to {} organisation.'
DEFAULT_SESSION_EXPIRY_TIME = 21600  # 6 hours
DEFAULT_TEMP_TOKEN_EXPIRY_TIME = 21600  # 6 hours

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGE_ME!!!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    # admin tool apps
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.gis',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'markdown_deux',
    'bootstrapform',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
    'admin_tools_stats',
    'genericadmin',
    'mailer',
    'registration',
    'django_nose',
    'django_digest',
    'oauth2_provider',
    'rest_framework.authtoken',
    'taggit',
    'onadata.apps.logger',
    'onadata.apps.viewer',
    'onadata.apps.main',
    'onadata.apps.restservice',
    'onadata.apps.api',
    'onadata.apps.sms_support',
    'onadata.libs',
    'reversion',
    'actstream',
    'guardian',
    'djangobower',
    'django_nvd3',
    'notifications',
    'avatar',
    'crispy_forms',
    'django_tables2',
    'debug_toolbar',
    'rest_framework',
    'selectable',
    'faq',
    'helpdesk',
    # 'messaging',
    'corsheaders',
    'onadata.apps.messaging.apps.MessagingConfig',
    'helpline',
    'mathfilters',
    )

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
        'groups': 'Access to your groups'}
}
# needed by guardian
ANONYMOUS_DEFAULT_USERNAME = 'AnonymousUser'

REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
    'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'onadata.libs.authentication.DigestAuthentication',
        'onadata.libs.authentication.TempTokenAuthentication',
        'onadata.libs.authentication.EnketoTokenAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_jsonp.renderers.JSONPRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    ),
}

SWAGGER_SETTINGS = {
    "exclude_namespaces": [],    # List URL namespaces to ignore
    "api_version": '1.0',  # Specify your API's version (optional)
    "enabled_methods": [         # Methods to enable in UI
        'get',
        'post',
        'put',
        'patch',
        'delete'
    ],
}

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (
    'dev.ona.io',
)
CORS_URLS_ALLOW_ALL_REGEX = (
    r'^/api/v1/osm/.*$',
)

USE_THOUSAND_SEPARATOR = True

COMPRESS = True

# extra data stored with users
AUTH_PROFILE_MODULE = 'onadata.apps.main.UserProfile'

# case insensitive usernames
AUTHENTICATION_BACKENDS = (
    'onadata.apps.main.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# Settings for Django Registration
ACCOUNT_ACTIVATION_DAYS = 1


def skip_suspicious_operations(record):
    """Prevent django from sending 500 error
    email notifications for SuspiciousOperation
    events, since they are not true server errors,
    especially when related to the ALLOWED_HOSTS
    configuration

    background and more information:
    http://www.tiwoc.de/blog/2013/03/django-prevent-email-notification-on-susp\
    iciousoperation/
    """
    if record.exc_info:
        exc_value = record.exc_info[1]
        if isinstance(exc_value, SuspiciousOperation):
            return False
    return True


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s' +
                      ' %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'profiler': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'sql': {
            'format': '%(levelname)s %(process)d %(thread)d' +
                      ' %(time)s seconds %(message)s %(sql)s'
        },
        'sql_totals': {
            'format': '%(levelname)s %(process)d %(thread)d %(time)s seconds' +
                      ' %(message)s %(num_queries)s sql queries'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        # Define filter for suspicious urls
        'skip_suspicious_operations': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_suspicious_operations,
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false', 'skip_suspicious_operations'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout
        },
        'audit': {
            'level': 'DEBUG',
            'class': 'onadata.libs.utils.log.AuditLogHandler',
            'formatter': 'verbose',
            'model': 'onadata.apps.main.models.audit.AuditLog'
        },
        # 'sql_handler': {
        #     'level': 'DEBUG',
        #     'class': 'logging.StreamHandler',
        #     'formatter': 'sql',
        #     'stream': sys.stdout
        # },
        # 'sql_totals_handler': {
        #     'level': 'DEBUG',
        #     'class': 'logging.StreamHandler',
        #     'formatter': 'sql_totals',
        #     'stream': sys.stdout
        # }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'console_logger': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'audit_logger': {
            'handlers': ['audit'],
            'level': 'DEBUG',
            'propagate': True
        },
        # 'sql_logger': {
        #     'handlers': ['sql_handler'],
        #     'level': 'DEBUG',
        #     'propagate': True
        # },
        # 'sql_totals_logger': {
        #     'handlers': ['sql_totals_handler'],
        #     'level': 'DEBUG',
        #     'propagate': True
        # }
    }
}

# PROFILE_API_ACTION_FUNCTION is used to toggle profiling a viewset's action
PROFILE_API_ACTION_FUNCTION = False
PROFILE_LOG_BASE = '/tmp/'

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'onadata.libs.utils.middleware.LocaleMiddlewareWithTweaks',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'myhelpline.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.tz',
                'onadata.apps.main.context_processors.google_analytics',
                'onadata.apps.main.context_processors.site_name',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
            ],
            'loaders': [
                'admin_tools.template_loaders.Loader',
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]


def configure_logging(logger, **kwargs):
    admin_email_handler = AdminEmailHandler()
    admin_email_handler.setLevel(logging.ERROR)
    logger.addHandler(admin_email_handler)


after_setup_logger.connect(configure_logging)

GOOGLE_STEP2_URI = 'http://helpline.co.ke/gwelcome'
GOOGLE_OAUTH2_CLIENT_ID = 'REPLACE ME'
GOOGLE_OAUTH2_CLIENT_SECRET = 'REPLACE ME'

THUMB_CONF = {
    'large': {'size': 1280, 'suffix': '-large'},
    'medium': {'size': 640, 'suffix': '-medium'},
    'small': {'size': 240, 'suffix': '-small'},
}
# order of thumbnails from largest to smallest
THUMB_ORDER = ['large', 'medium', 'small']
IMG_FILE_TYPE = 'jpg'

# celery
CELERY_TASK_ALWAYS_EAGER = False
CELERY_IMPORTS = ('onadata.libs.utils.csv_import',)

CSV_FILESIZE_IMPORT_ASYNC_THRESHOLD = 100000  # Bytes
GOOGLE_SHEET_UPLOAD_BATCH = 1000

# duration to keep zip exports before deletion (in seconds)
ZIP_EXPORT_COUNTDOWN = 3600  # 1 hour

# number of records on export or CSV import before a progress update
EXPORT_TASK_PROGRESS_UPDATE_BATCH = 1000
EXPORT_TASK_LIFESPAN = 6  # six hours

# default content length for submission requests
DEFAULT_CONTENT_LENGTH = 10000000

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--with-fixture-bundling', '--nologcapture', '--nocapture']

# fake endpoints for testing
TEST_HTTP_HOST = 'testserver.com'
TEST_USERNAME = 'bob'

# specify the root folder which may contain a templates folder and a static
# folder used to override templates for site specific details
TEMPLATE_OVERRIDE_ROOT_DIR = None

# Use 1 or 0 for multiple selects instead of True or False for csv, xls exports
BINARY_SELECT_MULTIPLES = False

# Use 'n/a' for empty values by default on csv exports
NA_REP = 'n/a'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

if isinstance(TEMPLATE_OVERRIDE_ROOT_DIR, basestring):
    # site templates overrides
    TEMPLATES[0]['DIRS'] = [
        os.path.join(PROJECT_ROOT, TEMPLATE_OVERRIDE_ROOT_DIR, 'templates'),
    ] + TEMPLATES[0]['DIRS']
    # site static files path
    STATICFILES_DIRS += (
        os.path.join(PROJECT_ROOT, TEMPLATE_OVERRIDE_ROOT_DIR, 'static'),
    )

# Set wsgi url scheme to HTTPS
# os.environ['wsgi.url_scheme'] = 'https'

SUPPORTED_MEDIA_UPLOAD_TYPES = [
    'audio/mp3',
    'audio/mpeg',
    'audio/wav',
    'audio/x-m4a',
    'image/jpeg',
    'image/png',
    'image/svg+xml',
    'text/csv',
    'text/json',
    'video/3gpp',
    'video/mp4',
    'application/json',
    'application/pdf',
    'application/msword',
    'application/vnd.ms-excel',
    'application/vnd.ms-powerpoint',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.oasis.opendocument.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.presentationml.\
     presentation',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/zip',
]

CSV_ROW_IMPORT_ASYNC_THRESHOLD = 100
SEND_EMAIL_ACTIVATION_API = False
METADATA_SEPARATOR = "|"

PARSED_INSTANCE_DEFAULT_LIMIT = 1000000
PARSED_INSTANCE_DEFAULT_BATCHSIZE = 1000

PROFILE_SERIALIZER = \
    "onadata.libs.serializers.user_profile_serializer.UserProfileSerializer"
ORG_PROFILE_SERIALIZER = \
    "onadata.libs.serializers.organization_serializer.OrganizationSerializer"
BASE_VIEWSET = "onadata.libs.baseviewset.DefaultBaseViewset"

path = os.path.join(PROJECT_ROOT, "..", "extras", "reserved_accounts.txt")

EXPORT_WITH_IMAGE_DEFAULT = True

try:
    with open(path, 'r') as f:
        RESERVED_USERNAMES = [line.rstrip() for line in f]
except EnvironmentError:
    RESERVED_USERNAMES = []

STATIC_DOC = '/static/docs/index.html'

try:
    HOSTNAME = socket.gethostname()
except Exception:
    HOSTNAME = 'localhost'

CACHE_MIXIN_SECONDS = 60

TAGGIT_CASE_INSENSITIVE = True

DEFAULT_CELERY_MAX_RETIRES = 3
DEFAULT_CELERY_INTERVAL_START = 2
DEFAULT_CELERY_INTERVAL_MAX = 0.5
DEFAULT_CELERY_INTERVAL_STEP = 0.5

# legacy setting for old sites who still use a local_settings.py file and have
# not updated to presets/
WSGI_APPLICATION = 'myhelpline.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'helpline',
        'USER': 'helplineuser',
        'PASSWORD': 'helplinepasswd',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

LANGUAGES = (
    ('fr', u'Français'),
    ('en', u'English'),
    ('es', u'Español'),
    ('it', u'Italiano'),
    ('km', u'ភាសាខ្មែរ'),
    ('ne', u'नेपाली'),
    ('nl', u'Nederlands'),
    ('sw', u'Swahili'),
    ('zh-cn', u'简体中文'),
)

LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'), )

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

# Enketo URL
ENKETO_PROTOCOL = 'http'
ENKETO_URL = 'https://enketo.bitz-itc.com'
ENKETO_API_SURVEY_PATH = '/api/v2/survey'
ENKETO_API_INSTANCE_PATH = '/api/v2/instance'
ENKETO_PREVIEW_URL = urljoin(ENKETO_URL, ENKETO_API_SURVEY_PATH + '/preview')
ENKETO_API_TOKEN = ''
ENKETO_API_INSTANCE_IFRAME_URL = ENKETO_URL + "api/v2/instance/iframe"
ENKETO_API_SALT = 'secretsalt'
VERIFY_SSL = True

MEDIA_ROOT = "/var/www/html/media/"
MEDIA_URL = "/media/"

AVATAR_CACHE_ENABLED = False

# Django bower settings requirements.
BOWER_COMPONENTS_ROOT = os.path.join(BASE_DIR, "components/")

BOWER_INSTALLED_APPS = (
    'd3#3.4.13',
    'nvd3#1.7.1',
    'admin-lte#v2.3.7',
    'bootstrap#v3.3.7',
    'bootstrap-datepicker#1.6.4',
    'bootstrap3-wysiwyg',
    'jquery#2.2.3',
    'jquery-ui#~1.10.3',
    'jvectormap#1.2.2',
    'ionicons#2.0.1',
    'clipboard#1.5.15',
    'dimple#1.1.3',
    'backgrid#~0.3.5',
    'backgrid-filter#~0.3.5',
    'backgrid-paginator#~0.3.5',
    'font-awesome#4.7.0',
    'bootstrap-daterangepicker#2.1.25',
    'moment#2.18.1',
    'easytimer.js#2.2.3',
    "datatables.net-buttons#^1.5.3",
    "pdfmake#^0.1.38",
    "jszip#^3.1.5"

)

STATICFILES_FINDERS = ['djangobower.finders.BowerFinder',
                       'django.contrib.staticfiles.finders.FileSystemFinder',
                       'django.contrib.staticfiles.finders.AppDirectoriesFinder']

INTERNAL_IPS = '192.168.86.1'

SHORT_DATETIME_FORMAT = 'Y N j, H:i:s.u'
DATETIME_FORMAT = 'Y N j, H:i:s.u'
TIME_FORMAT = 'H:i:s'

ADMIN_SITE_HEADER = 'Administration'

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'

# Default service used to report filters
DEFAULT_SERVICE = 'Inbound'

# Default dispositions.
DISPOSITION_CHOICES = (
    ('--', 'Dispose'),
    ('Feedback', 'Feedback'),
    ('Inquiry', 'Inquiry'),
    ('Complaint', 'Complaint'),
    ('Transfer', 'Transfer'),
    ('Silent Call', 'Silent Call'),
    ('Dropped', 'Dropped'),
    ('Prank', 'Prank'),
    ('Insufficient Information', 'Insufficient Information'),
)

BLACKBOX_API_KEY = ''
BLACKBOX_API_SIGNATURE = ''
BLACKBOX_SHORT_CODE = ''
BLACKBOX_KEYWORD = ''

AFRICASTALKING_API_KEY = ''
AFRICASTALKING_API_USERNAME = ''

SENDSMS_BACKEND = 'custom_sms_backend.custom.AfricasTalkingSmsBackend'

SITE_ID = 1

# EMAIL_BACKEND = "mailer.backend.DbBackend"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Email will be sent to Help Desk Emails on Escalation.
HELPDESK_EMAILS = []


ADMIN_TOOLS_MENU = 'custom_admin_tools.menu.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = 'custom_admin_tools.dashboard.CustomIndexDashboard'

ADMIN_TOOLS_THEMING_CSS = 'helpline/css/theming.css'

CORS_ORIGIN_WHITELIST = (
    'localhost:5000',
    '127.0.0.1:5000'
)

SALESFORCE_URL = ''
SALESFORCE_ORGID = ''

SALESFORCE_LEAD_URL = ""
SALESFORCE_LEAD_ORGID = ""

HELPLINE_SPOOL_DIR = ''

TESTING_MODE = True

SLAVE_DATABASES = []

try:
    from myhelpline.localsettings import *
except ImportError as e:
    print(e)
    pass
