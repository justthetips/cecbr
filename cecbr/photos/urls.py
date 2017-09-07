from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView, ListView
from django.views import defaults as default_views
from django.core.urlresolvers import reverse

from .views import season_view, AlbumDetailView, PhotoDetailView, GroupListView, CreateGroupView, CreatePersonView, PersonListView, GroupDetailView

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
    url(regex=r'^photo/(?P<pk>[-\w]+)/$',
        view=PhotoDetailView.as_view(),
        name="photo_detail"
    ),
    url(regex=r'^groups/$',
        view = GroupListView.as_view(),
        name='groups'),
    url(regex=r'^groups/create/$',
        view=CreateGroupView.as_view(success_url='/photos/groups/'),
        name='create_group'),
    url(regex=r'^groups/(?P<pk>[-\w]+)/$',
        view = GroupDetailView.as_view(),
        name='group_detail'),
    url(regex=r'^people/$',
        view=PersonListView.as_view(),
        name='people'),
    url(regex=r'^people/create$',
        view=CreatePersonView.as_view(success_url='/photos/people/'),
        name='create_person'),

]
