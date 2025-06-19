"""
WSGI config for ai_support project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_support.settings')

# Get the original Django application
django_app = get_wsgi_application()

def health_check_app(environ, start_response):
    """Simple health check that bypasses Django entirely"""
    if environ.get('PATH_INFO') == '/health/':
        status = '200 OK'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return [b'OK']
    else:
        return django_app(environ, start_response)

# Use our health check wrapper
application = health_check_app 