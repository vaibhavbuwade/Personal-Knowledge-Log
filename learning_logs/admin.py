from django.contrib import admin
from .models import (
    Topic, Entry, Summary, Quiz, Question, Choice,
    QuizAttempt, ChatSession, ChatMessage
)


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


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('entry', 'user', 'is_mock', 'created_at')
    list_filter = ('is_mock', 'created_at', 'user')
    search_fields = ('entry__title', 'summary_text', 'user__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'order', 'text_preview')
    list_filter = ('quiz__user',)
    search_fields = ('text', 'explanation', 'quiz__title')
    inlines = [ChoiceInline]

    @admin.display(description='Question')
    def text_preview(self, obj):
        return obj.text[:60]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'entry', 'user', 'question_count', 'is_mock', 'created_at')
    list_filter = ('is_mock', 'created_at', 'user')
    search_fields = ('title', 'entry__title', 'user__username')
    date_hierarchy = 'created_at'
    inlines = [QuestionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total_questions', 'percentage_display', 'attempted_at')
    list_filter = ('attempted_at', 'user')
    search_fields = ('user__username', 'quiz__title')
    date_hierarchy = 'attempted_at'

    @admin.display(description='Score %')
    def percentage_display(self, obj):
        return f"{obj.percentage:.1f}%"


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'retrieved_notes', 'created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'user__username')
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at', 'session__user')
    search_fields = ('content', 'session__user__username')

    @admin.display(description='Content')
    def content_preview(self, obj):
        return obj.content[:80]


from .models import EmailOTP


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'attempts', 'max_attempts', 'is_used', 'is_expired_display', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('email', 'user__username')
    readonly_fields = ('otp_hash', 'created_at', 'expires_at')
    ordering = ('-created_at',)

    @admin.display(description='Expired?', boolean=True)
    def is_expired_display(self, obj):
        return obj.is_expired()
