from django.contrib import admin

from .models import Choice, Question, DataFile


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['question_text']}),
        ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    ]
    inlines = [ChoiceInline]
    list_display = ('question_text', 'pub_date', 'was_published_recently')
    list_filter = ['pub_date']
    search_fields = ['question_text']


admin.site.register(Question, QuestionAdmin)


class FileAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['filename']}),
        ('Date information', {'fields': ['date']}),
        ('Code', {'fields': ['tempCode']}),

    ]
    list_display = ('filename', 'date', 'tempCode')


admin.site.register(DataFile, FileAdmin)
