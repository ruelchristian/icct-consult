from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('directory/', include('directory.urls')),
    path('availability/', include('availability.urls')),
    path('bookings/', include('bookings.urls')),
    path('records/', include('records.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "ICCT Faculty Consultation System Admin"
admin.site.site_title = "ICCT Consultation Admin Portal"
admin.site.index_title = "System Management Portal"
