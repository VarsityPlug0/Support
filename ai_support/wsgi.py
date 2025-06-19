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
    path_info = environ.get('PATH_INFO', '')
    
    if path_info == '/health/':
        status = '200 OK'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return [b'OK']
    elif path_info == '/':
        # Redirect root to chat page
        status = '302 Found'
        response_headers = [('Location', '/chat/'), ('Content-Type', 'text/html')]
        start_response(status, response_headers)
        return [b'<html><head><title>Redirecting...</title></head><body><p>Redirecting to <a href="/chat/">chat</a>...</p></body></html>']
    else:
        return django_app(environ, start_response)

# Use our health check wrapper
application = health_check_app 