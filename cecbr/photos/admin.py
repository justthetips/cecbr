from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

from .models import CECBRProfile, Season, Album, Photo, Group, Person, TrainingPhoto


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
    list_display = ('season_name', 'album_count', 'created', 'modified')


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    model = Album
    list_display = ('album_name', 'season', 'count', 'album_date', 'processed', 'analyzed', 'created', 'modified')
    list_filter = ('season',)
    search_fields = ('album_name', 'id')
