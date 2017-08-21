from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views

from .views import season_view, AlbumDetailView

urlpatterns = [
    url(
        regex=r'^$',
        view=TemplateView.as_view(template_name='photos/photo_main.html'),
        name='photo_main'
    ),
    url(
        regex=r'^season/$',
        view=season_view,
        name='season_index'
    ),
    url(regex=r'^album/(?P<pk>[-\w]+)/$',
        view=AlbumDetailView.as_view(),
        name="album_detail"
    ),
]
