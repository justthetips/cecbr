from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

from .models import CECBRProfile, Season, Album, Photo, Group, Person, TrainingPhoto


def handle_season(modeladmin, request, queryset):
    cp = request.user.cecbrprofile
    for season in queryset:
        season.process_season(cp)

def handle_album(modeladmin, request, queryset):
    cp = request.user.cecbrprofile
    for album in queryset:
        album.process_album(cp)


@admin.register(CECBRProfile)
class CECBRProfileAdmin(admin.ModelAdmin):
    model = CECBRProfile

    list_display = ('get_user_name', 'created', 'modified', 'last_album_view')

    def get_user_name(self, obj):
        return obj.user.name

    get_user_name.short_description = 'Name'
    get_user_name.admin_order_field = 'cecbrprofile.user'


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    model = Season
    list_display = ('season_name', 'album_count', 'photo_count', 'created', 'modified')
    actions = [handle_season]


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    model = Album
    list_display = ('album_name', 'season', 'count', 'album_date', 'processed', 'analyzed', 'created', 'modified')
    list_filter = ('season',)
    search_fields = ('album_name', 'album_id')
    actions = [handle_album]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    model = Photo
    list_display = (
    'photo_id', 'album', 'analyzed', 'identified', 'analyzed_date', 'identified_date', 'created', 'modified')
    list_filter = ('album',)
    search_fields = ('photo_id', 'album')
