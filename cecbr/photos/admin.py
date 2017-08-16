from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

from .models import CECBRProfile

@admin.register(CECBRProfile)
class CECBRProfileAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'created', 'modified', 'last_album_view')

    def get_user_name(self, obj):
        return obj.user.name

    get_user_name.short_description = 'Name'
    get_user_name.admin_order_field = 'cecbrprofile.user'

