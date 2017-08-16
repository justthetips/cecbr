from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

from .models import CECBRProfile

@admin.register(CECBRProfile)
class CECBRProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified', 'last_album_view')
    
