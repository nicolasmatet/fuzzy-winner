"""
WSGI config for djangoSite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/var/www/DjanoSiteProject/djangoSite')
sys.path.append('/var/www/DjanoSiteProject/DjangoSiteEnv/lib/python3.4//site-packages')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoSite.settings")

application = get_wsgi_application()
