from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('ework_user_tg.urls', namespace='users')),
    path('rosetta/', include('rosetta.urls')),
    path('jobs/', include('ework_job.urls', namespace='jobs')),
    path('services/', include('ework_services.urls')),
    path('modal-select-post/', views.modal_select_post, name='modal_select_post'),
    path("", views.HomeView.as_view(), name='home'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
