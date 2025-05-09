
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns


urlpatterns = [
    path('admin/', admin.site.urls),
    path('services/', include('ework_services.urls', namespace='services')),
    path('jobs/', include('ework_job.urls', namespace='jobs')),
    path('users/', include('ework_user_tg.urls', namespace='users')),
    path('rosetta/', include('rosetta.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

