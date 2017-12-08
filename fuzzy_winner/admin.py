from django.contrib import admin

from .models import DataFile


class FileAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['filename']}),
        ('Date information', {'fields': ['date']}),
        ('Code', {'fields': ['tempCode']}),

    ]
    list_display = ('filename', 'date', 'tempCode')


admin.site.register(DataFile, FileAdmin)
