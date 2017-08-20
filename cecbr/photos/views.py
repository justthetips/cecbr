from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

import django.utils.timezone

from .models import Season, Album

@login_required()
def season_view(request: HttpRequest) -> HttpResponse:
    s = request.session.get('season', '2017')
    season = Season.objects.get(season_name = s)
    cp = request.user.cecbrprofile

    albums = Album.objects.filter(season=season)

    new_albums = []
    old_albums = []

    for album in albums:
        if album.processed_date is not None:
            if album.processed_date >= cp.last_album_view:
                new_albums.append(album)
            else:
                old_albums.append(album)

    cp.last_album_view = django.utils.timezone.now()
    context = {'new_albums': new_albums, 'old_albums': old_albums, 'season': s}
    return render(request, 'photos/season_index.html', context)


