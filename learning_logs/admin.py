from django.contrib import admin
from .models import Topic, Entry


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'get_entry_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)

    @admin.display(description='Entries Count')
    def get_entry_count(self, obj):
        return obj.entries.count()


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'get_author', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'topic__user')
    search_fields = ('title', 'content', 'topic__title', 'topic__user__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    @admin.display(description='Author')
    def get_author(self, obj):
        return obj.topic.user.username
