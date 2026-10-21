from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Topic(models.Model):
    """A topic the user is learning about or logging notes for."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topics',
        help_text="The user who created and owns this topic."
    )
    title = models.CharField(
        max_length=200,
        help_text="Enter a clear, descriptive topic name (e.g., Python Basics, System Design)."
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description or overview of this learning topic."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('learning_logs:topic_detail', kwargs={'topic_id': self.pk})

    @property
    def entry_count(self):
        return self.entries.count()


class Entry(models.Model):
    """Specific learning note or journal entry created under a topic."""
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='entries',
        help_text="The topic this learning entry belongs to."
    )
    title = models.CharField(
        max_length=200,
        help_text="Enter a title summarizing what you learned in this entry."
    )
    content = models.TextField(
        help_text="Detailed notes, code snippets, takeaways, or concepts learned."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Learning Entry'
        verbose_name_plural = 'Learning Entries'
        indexes = [
            models.Index(fields=['topic', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.topic.title}"

    def snippet(self, max_length=120):
        """Return a truncated preview of the entry content."""
        if len(self.content) > max_length:
            return self.content[:max_length].rstrip() + '...'
        return self.content


class Summary(models.Model):
    """AI-generated summary and key takeaways for a learning entry."""
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE,
        related_name='summaries',
        help_text="The learning entry this summary was generated from."
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='summaries',
        help_text="The user who generated and owns this summary."
    )
    summary_text = models.TextField(
        help_text="Concise, plain-language summary of the note."
    )
    key_points = models.TextField(
        blank=True,
        help_text="Newline-delimited or JSON list of key points and takeaways."
    )
    key_terms = models.TextField(
        blank=True,
        help_text="Newline-delimited or JSON list of terminology and definitions."
    )
    is_mock = models.BooleanField(
        default=True,
        help_text="Indicates whether this summary was generated via Mock AI demo mode."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Entry Summary'
        verbose_name_plural = 'Entry Summaries'

    def __str__(self):
        return f"Summary for: {self.entry.title}"

    def get_points_list(self):
        """Helper to return key points as a clean python list."""
        if not self.key_points:
            return []
        return [p.strip() for p in self.key_points.split('\n') if p.strip()]

    def get_terms_list(self):
        """Helper to return key terms as a clean python list."""
        if not self.key_terms:
            return []
        return [t.strip() for t in self.key_terms.split('\n') if t.strip()]


class Quiz(models.Model):
    """AI-generated quiz linked to a specific learning entry."""
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE,
        related_name='quizzes',
        help_text="The learning entry this quiz tests."
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quizzes',
        help_text="The user who owns this quiz."
    )
    title = models.CharField(
        max_length=255,
        help_text="Descriptive title of the quiz."
    )
    is_mock = models.BooleanField(
        default=True,
        help_text="Indicates whether this quiz was generated in mock demo mode."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'

    def __str__(self):
        return f"{self.title} ({self.entry.title})"

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def highest_score(self):
        attempt = self.attempts.order_by('-percentage').first()
        return attempt.percentage if attempt else None


class Question(models.Model):
    """A multiple-choice question in a quiz."""
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.TextField(help_text="The question prompt.")
    explanation = models.TextField(
        blank=True,
        help_text="Explanation of the correct answer shown after submission."
    )
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class Choice(models.Model):
    """An option for a multiple-choice question."""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.CharField(max_length=500, help_text="Choice text.")
    is_correct = models.BooleanField(
        default=False,
        help_text="Whether this is the correct answer."
    )
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'

    def __str__(self):
        return f"{self.text[:40]} ({'Correct' if self.is_correct else 'Incorrect'})"


class QuizAttempt(models.Model):
    """Record of a user taking a quiz with server-side computed score."""
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    score = models.PositiveIntegerField(help_text="Number of correct questions.")
    total_questions = models.PositiveIntegerField(help_text="Total number of questions.")
    percentage = models.FloatField(default=0.0, help_text="Calculated percentage score.")
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}: {self.score}/{self.total_questions} ({self.percentage:.1f}%)"


class ChatSession(models.Model):
    """A conversational session between the user and 'Ask My Notes' AI."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    title = models.CharField(max_length=200, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class ChatMessage(models.Model):
    """A single exchange in a chat session."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    retrieved_notes = models.TextField(
        blank=True,
        help_text="Titles or excerpts of notes retrieved from user storage as context."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"[{self.role.upper()}] {self.content[:40]}"
