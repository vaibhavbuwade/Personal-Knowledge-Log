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


import hmac
import hashlib
import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


class EmailOTP(models.Model):
    """
    Cryptographically secure, single-use, 5-minute Email OTP challenge for dual login.
    Stores HMAC-SHA256 hash with SECRET_KEY to avoid storing raw OTP digits.
    """
    email = models.EmailField(db_index=True, help_text="Email address the OTP was generated for.")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='otp_challenges',
        help_text="User matched to this email, if registered."
    )
    otp_hash = models.CharField(max_length=128, help_text="HMAC-SHA256 digest of the 6-digit OTP.")
    attempts = models.PositiveIntegerField(default=0, help_text="Verification attempts made.")
    max_attempts = models.PositiveIntegerField(default=5, help_text="Max allowed failed attempts before lockout.")
    is_used = models.BooleanField(default=False, help_text="Whether this OTP was verified.")
    expires_at = models.DateTimeField(help_text="Expiry time (5 minutes).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email OTP Challenge'
        verbose_name_plural = 'Email OTP Challenges'
        indexes = [
            models.Index(fields=['email', '-created_at']),
        ]

    def __str__(self):
        status = "Used" if self.is_used else ("Expired" if self.is_expired() else "Active")
        return f"OTP for {self.email} ({status}) - {self.attempts}/{self.max_attempts} attempts"

    @classmethod
    def compute_hmac(cls, otp_str: str) -> str:
        """Derives a secure HMAC-SHA256 signature using Django SECRET_KEY."""
        secret = settings.SECRET_KEY.encode('utf-8')
        return hmac.new(secret, otp_str.strip().encode('utf-8'), hashlib.sha256).hexdigest()

    @classmethod
    def check_resend_cooldown(cls, email: str, cooldown_seconds: int = 60) -> int:
        """
        Returns remaining seconds if email is currently in cooldown, or 0 if allowed to send.
        """
        last_otp = cls.objects.filter(email__iexact=email.strip().lower()).order_by('-created_at').first()
        if last_otp:
            elapsed = (timezone.now() - last_otp.created_at).total_seconds()
            if elapsed < cooldown_seconds:
                return int(cooldown_seconds - elapsed)
        return 0

    @classmethod
    def create_challenge(cls, email: str, user=None) -> tuple['EmailOTP', str]:
        """
        Invalidates existing active challenges for this email, generates a cryptographically
        secure 6-digit OTP using secrets, and stores its HMAC digest with a 5-minute expiry.
        """
        clean_email = email.strip().lower()
        # Invalidate any prior unused OTPs for this email
        cls.objects.filter(email__iexact=clean_email, is_used=False).update(is_used=True)

        raw_otp = "".join(secrets.choice("0123456789") for _ in range(6))
        otp_hash = cls.compute_hmac(raw_otp)
        expires_at = timezone.now() + timedelta(minutes=5)

        challenge = cls.objects.create(
            email=clean_email,
            user=user,
            otp_hash=otp_hash,
            expires_at=expires_at
        )
        return challenge, raw_otp

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def is_locked(self) -> bool:
        return self.attempts >= self.max_attempts

    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired() and not self.is_locked()

    def verify(self, candidate_otp: str) -> tuple[bool, str]:
        """
        Validates candidate OTP with constant-time comparison, incrementing attempts.
        Returns (success_bool, message_str).
        """
        if self.is_used:
            return False, "This OTP has already been used. Please request a new code."
        if self.is_expired():
            return False, "This OTP has expired (5-minute limit). Please request a new code."
        if self.is_locked():
            return False, "Too many failed attempts. This OTP is locked. Please request a new code."

        self.attempts += 1
        candidate_hash = self.compute_hmac(candidate_otp)

        # Constant-time comparison to mitigate timing attacks
        if hmac.compare_digest(self.otp_hash, candidate_hash):
            self.is_used = True
            self.save(update_fields=['attempts', 'is_used'])
            return True, "Verification successful."
        else:
            self.save(update_fields=['attempts'])
            remaining = max(0, self.max_attempts - self.attempts)
            if remaining == 0:
                return False, "Too many incorrect attempts. This OTP has been locked."
            return False, f"Incorrect OTP code. {remaining} attempt{'s' if remaining != 1 else ''} remaining."
