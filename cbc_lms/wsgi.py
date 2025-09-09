# #cbc_lms/cbc_lms
# """
# WSGI config for cbc_lms project.

# It exposes the WSGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
# """

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cbc_lms.settings')

application = get_wsgi_application()






