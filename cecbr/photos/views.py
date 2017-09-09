import os
import zipfile
from io import BytesIO
import json

import django.utils.timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.text import slugify
from django.views.generic import DetailView, ListView, CreateView

from .forms import GroupForm, PersonForm
from .models import Season, Album, Photo, Group, Person, CECBRProfile, VaultedPhoto


@login_required()
def season_view(request: HttpRequest) -> HttpResponse:
    s = request.session.get('season', '2017')
    season = Season.objects.get(season_name=s)
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


class AlbumDetailView(LoginRequiredMixin, DetailView):
    model = Album

    def get_context_data(self, **kwargs):
        context = super(AlbumDetailView, self).get_context_data(**kwargs)
        context['album'] = self.object
        context['photos'] = Photo.objects.filter(album=self.object)
        return context


class PhotoDetailView(LoginRequiredMixin, DetailView):
    model = Photo


class CreateGroupView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "photos/group_form.html"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = CECBRProfile.objects.get(user=self.request.user)
        return super(CreateGroupView, self).form_valid(form)


class CreatePersonView(LoginRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = 'photos/people_form.html'

    def get_form_kwargs(self):
        kwargs = super(CreatePersonView, self).get_form_kwargs()
        kwargs['instance'] = CECBRProfile.objects.get(user=self.request.user)
        return kwargs


class GroupListView(LoginRequiredMixin, ListView):
    model = Group


class PersonListView(LoginRequiredMixin, ListView):
    model = Person
    template_name = 'photos/people_list.html'


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = "photos/group_detail.html"


@login_required()
def favorite_season_view(request):
    cp = request.user.cecbrprofile
    available_seasons = []
    for p in VaultedPhoto.objects.filter(user=cp).order_by('photo__album__season__season_name').distinct(
        'photo__album__season__season_name'):
        available_seasons.append(p.photo.album.season.season_name)

    context = {'available_seasons': available_seasons}
    return render(request, 'photos/vault_index.html', context)


@login_required()
def favorite_season_download(request, season_name):
    cp = request.user.cecbrprofile
    b = BytesIO()
    # The zip compressor
    zip_subdir = season_name
    zf = zipfile.ZipFile(b, "w")
    # the zip file name
    zip_filename = "{}_favorites_{}.zip".format(slugify(cp.user.name), season_name)

    q = VaultedPhoto.objects.filter(user=cp).filter(photo__album__season__season_name=season_name)
    for p in q:
        fdir, fname = os.path.split(p.large_photo.path)
        zf.write(p.large_photo.path, fname, zipfile.ZIP_DEFLATED)

    zf.close()

    resp = HttpResponse(b.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename={}'.format(zip_filename)

    return resp


@login_required()
def vault_season_list(request, season_name):
    cp = request.user.cecbrprofile
    q = VaultedPhoto.objects.filter(user=cp).filter(photo__album__season__season_name=season_name)
    context = {'photos': q, 'season_name': season_name}
    return render(request, 'photos/favorite_index.html', context)


@login_required()
def vaulted_photo(request, photoid):
    vp = VaultedPhoto.objects.get(uuid=photoid)
    p = vp.photo
    if not p.analyzed:
        p.analyze_photo()
    r = json.loads(p.face_json)['locations']
    rects={}
    for i, v in r.items():
        top, right, bottom, left = v
        rects[i] = [top,right,bottom-top,right-left]
    context = {'vp': vp, 'p': p, 'rects': rects}
    return render(request, 'photos/favorite_photo.html', context)
