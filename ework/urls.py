from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),
    path('admin/', admin.site.urls),
    path('users/', include('ework_user_tg.urls', namespace='users')),
    path('jobs/', include('ework_job.urls', namespace='jobs')),
    path('services/', include('ework_services.urls')),
    path('payments/', include('ework_payment.urls')),
    path("", include('ework_core.urls', namespace='core')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
