from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('about/', include('about.urls', namespace='about')),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('posts.urls', namespace='posts')),
]


handler403 = ''
handler404 = 'core.views.page_not_found'
handler500 = ''


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
