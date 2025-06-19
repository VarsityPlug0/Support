"""
URL configuration for ai_support project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
from core.views import test_openai_api

def simple_health_check(request):
    """Simple health check for Render - bypasses all middleware"""
    response = HttpResponse("OK")
    response["Content-Type"] = "text/plain"
    return response

def simple_root_page(request):
    """Simple root page that redirects to the main app"""
    from django.shortcuts import redirect
    return redirect('/chat/')

def api_test_view(request):
    """Test OpenAI API endpoint"""
    test_result = test_openai_api()
    return JsonResponse(test_result)

urlpatterns = [
    path('health/', simple_health_check, name='health_check'),  # Health check at root level
    path('api-test/', api_test_view, name='api_test'),  # API test endpoint
    path('admin/', admin.site.urls),  # Django admin interface
    path('', simple_root_page, name='root'),  # Simple root page
    path('', include('core.urls')),   # Include core app URLs
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 