from django.contrib import admin

from .models import AnalysisGroup, AnalysisPhoto

@admin.register(AnalysisGroup)
class GroupAdmin(admin.ModelAdmin):
    model = AnalysisGroup
    list_display = ('id', 'group', 'trained', 'trained_date', 'created', 'modified')
    search_fields = ('group',)

@admin.register(AnalysisPhoto)
class PhotoAdmin(admin.ModelAdmin):
    model = AnalysisPhoto
    list_display = ('id','detected', 'faced', 'created', 'modified' )
    list_filter = ('group','detected','faced')

