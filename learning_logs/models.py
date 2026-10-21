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

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('learning_logs:topic_detail', kwargs={'pk': self.pk})

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

    def __str__(self):
        return f"{self.title} - {self.topic.title}"

    def snippet(self, max_length=120):
        """Return a truncated preview of the entry content."""
        if len(self.content) > max_length:
            return self.content[:max_length].rstrip() + '...'
        return self.content
