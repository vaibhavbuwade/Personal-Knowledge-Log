from datetime import timedelta
from unittest import mock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import Topic, Entry, Summary, Quiz, Question, Choice, QuizAttempt, ChatSession, ChatMessage, EmailOTP
from .forms import TopicForm, EntryForm, UserRegistrationForm
from . import ai_service


class ModelTests(TestCase):
    """Test model methods, strings, and relationships."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='TestPassword123!'
        )
        self.topic = Topic.objects.create(
            user=self.user,
            title='Django Web Development',
            description='Learning Django models and views.'
        )
        self.entry = Entry.objects.create(
            topic=self.topic,
            title='MTV Architecture',
            content='Django follows the Model-Template-View architectural pattern.'
        )

    def test_topic_str(self):
        self.assertEqual(str(self.topic), 'Django Web Development')

    def test_entry_str(self):
        self.assertEqual(str(self.entry), 'MTV Architecture - Django Web Development')

    def test_topic_entry_count(self):
        self.assertEqual(self.topic.entry_count, 1)

    def test_entry_snippet(self):
        short_snippet = self.entry.snippet(max_length=20)
        self.assertTrue(short_snippet.endswith('...'))
        self.assertEqual(self.entry.snippet(max_length=200), self.entry.content)


class AuthenticationTests(TestCase):
    """Test user registration, login, and logout workflows."""

    def setUp(self):
        self.client = Client()

    def test_successful_registration(self):
        response = self.client.post(reverse('learning_logs:register'), {
            'username': 'newlearner',
            'email': 'newlearner@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:dashboard'))
        self.assertTrue(User.objects.filter(username='newlearner').exists())
        self.assertTrue(response.context['user'].is_authenticated)

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse('learning_logs:register'), {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())
        self.assertFormError(response.context['form'], 'password_confirm', 'Passwords do not match.')

    def test_registration_duplicate_username(self):
        User.objects.create_user(username='existinguser', email='a@example.com', password='Password123!')
        response = self.client.post(reverse('learning_logs:register'), {
            'username': 'existinguser',
            'email': 'b@example.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'This username is already taken. Please choose another.')

    def test_registration_duplicate_email(self):
        User.objects.create_user(username='userone', email='shared@example.com', password='Password123!')
        response = self.client.post(reverse('learning_logs:register'), {
            'username': 'usertwo',
            'email': 'shared@example.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'An account with this email address already exists.')

    def test_successful_login(self):
        User.objects.create_user(username='john', password='Password123!')
        response = self.client.post(reverse('learning_logs:login'), {
            'username': 'john',
            'password': 'Password123!',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:dashboard'))
        self.assertTrue(response.context['user'].is_authenticated)

    def test_invalid_login(self):
        User.objects.create_user(username='john', password='Password123!')
        response = self.client.post(reverse('learning_logs:login'), {
            'username': 'john',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_logout(self):
        user = User.objects.create_user(username='john', password='Password123!')
        self.client.force_login(user)
        response = self.client.post(reverse('learning_logs:logout'), follow=True)
        self.assertRedirects(response, reverse('learning_logs:login'))
        self.assertFalse(response.context['user'].is_authenticated)


class AccessControlAndOwnershipTests(TestCase):
    """Test @login_required protection and cross-user data isolation."""

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='alice', password='Password123!')
        self.user_b = User.objects.create_user(username='bob', password='Password123!')

        self.topic_a = Topic.objects.create(
            user=self.user_a,
            title="Alice's Secret Topic",
            description="Alice's private learning notes."
        )
        self.entry_a = Entry.objects.create(
            topic=self.topic_a,
            title="Alice's Entry",
            content="Alice's secret content."
        )

    def test_unauthenticated_redirects(self):
        """Unauthenticated requests must be redirected to login page."""
        protected_urls = [
            reverse('learning_logs:dashboard'),
            reverse('learning_logs:topic_list'),
            reverse('learning_logs:topic_create'),
            reverse('learning_logs:topic_detail', kwargs={'topic_id': self.topic_a.id}),
            reverse('learning_logs:topic_edit', kwargs={'topic_id': self.topic_a.id}),
            reverse('learning_logs:topic_delete', kwargs={'topic_id': self.topic_a.id}),
            reverse('learning_logs:topic_entry_create', kwargs={'topic_id': self.topic_a.id}),
            reverse('learning_logs:entry_create'),
            reverse('learning_logs:entry_edit', kwargs={'entry_id': self.entry_a.id}),
            reverse('learning_logs:entry_delete', kwargs={'entry_id': self.entry_a.id}),
            reverse('learning_logs:search'),
        ]
        login_url = reverse('learning_logs:login')

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"URL {url} did not redirect unauthenticated user")
            self.assertTrue(response.url.startswith(login_url), f"URL {url} did not redirect to {login_url}")

    def test_user_cannot_view_another_users_topic(self):
        """Bob should receive 404 when attempting to access Alice's topic."""
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('learning_logs:topic_detail', kwargs={'topic_id': self.topic_a.id}))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_edit_another_users_topic(self):
        """Bob cannot edit Alice's topic."""
        self.client.force_login(self.user_b)
        response = self.client.post(reverse('learning_logs:topic_edit', kwargs={'topic_id': self.topic_a.id}), {
            'title': 'Hacked Title',
            'description': 'Hacked description',
        })
        self.assertEqual(response.status_code, 404)
        self.topic_a.refresh_from_db()
        self.assertEqual(self.topic_a.title, "Alice's Secret Topic")

    def test_user_cannot_delete_another_users_topic(self):
        """Bob cannot delete Alice's topic."""
        self.client.force_login(self.user_b)
        response = self.client.post(reverse('learning_logs:topic_delete', kwargs={'topic_id': self.topic_a.id}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Topic.objects.filter(id=self.topic_a.id).exists())

    def test_user_cannot_add_entry_to_another_users_topic(self):
        """Bob cannot add an entry to Alice's topic."""
        self.client.force_login(self.user_b)
        response = self.client.post(reverse('learning_logs:topic_entry_create', kwargs={'topic_id': self.topic_a.id}), {
            'title': 'Intruder Entry',
            'content': 'Attempting unauthorized write.',
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.topic_a.entries.count(), 1)

    def test_user_cannot_edit_another_users_entry(self):
        """Bob cannot edit Alice's entry."""
        self.client.force_login(self.user_b)
        response = self.client.post(reverse('learning_logs:entry_edit', kwargs={'entry_id': self.entry_a.id}), {
            'title': 'Compromised Entry',
            'content': 'Compromised content',
        })
        self.assertEqual(response.status_code, 404)
        self.entry_a.refresh_from_db()
        self.assertEqual(self.entry_a.title, "Alice's Entry")

    def test_user_cannot_delete_another_users_entry(self):
        """Bob cannot delete Alice's entry."""
        self.client.force_login(self.user_b)
        response = self.client.post(reverse('learning_logs:entry_delete', kwargs={'entry_id': self.entry_a.id}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Entry.objects.filter(id=self.entry_a.id).exists())

    def test_topic_list_isolation(self):
        """Topic list only displays topics owned by current user."""
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('learning_logs:topic_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Alice's Secret Topic")


class TopicAndEntryCRUDTests(TestCase):
    """Test full CRUD workflows for topics and entries."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='charlie', password='Password123!')
        self.client.force_login(self.user)

    def test_create_topic(self):
        response = self.client.post(reverse('learning_logs:topic_create'), {
            'title': 'Algorithms',
            'description': 'Sorting, graphs, and dynamic programming.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        topic = Topic.objects.get(title='Algorithms')
        self.assertEqual(topic.user, self.user)
        self.assertEqual(topic.description, 'Sorting, graphs, and dynamic programming.')

    def test_edit_topic(self):
        topic = Topic.objects.create(user=self.user, title='Old Title', description='Old')
        response = self.client.post(reverse('learning_logs:topic_edit', kwargs={'topic_id': topic.id}), {
            'title': 'Updated Title',
            'description': 'Updated description',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        topic.refresh_from_db()
        self.assertEqual(topic.title, 'Updated Title')
        self.assertEqual(topic.description, 'Updated description')

    def test_delete_topic_cascades_entries(self):
        topic = Topic.objects.create(user=self.user, title='Topic to Delete')
        entry = Entry.objects.create(topic=topic, title='Entry to Delete', content='Bye')
        entry_id = entry.id

        response = self.client.post(reverse('learning_logs:topic_delete', kwargs={'topic_id': topic.id}), follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_list'))
        self.assertFalse(Topic.objects.filter(id=topic.id).exists())
        self.assertFalse(Entry.objects.filter(id=entry_id).exists())

    def test_create_entry_under_topic(self):
        topic = Topic.objects.create(user=self.user, title='Python Deep Dive')
        response = self.client.post(reverse('learning_logs:topic_entry_create', kwargs={'topic_id': topic.id}), {
            'title': 'Generators and Iterators',
            'content': 'yield produces an iterator generator.',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_detail', kwargs={'topic_id': topic.id}))
        self.assertTrue(Entry.objects.filter(title='Generators and Iterators', topic=topic).exists())

    def test_quick_create_entry(self):
        topic = Topic.objects.create(user=self.user, title='Database Fundamentals')
        response = self.client.post(reverse('learning_logs:entry_create'), {
            'topic': topic.id,
            'title': 'ACID Properties',
            'content': 'Atomicity, Consistency, Isolation, Durability.',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_detail', kwargs={'topic_id': topic.id}))
        self.assertTrue(Entry.objects.filter(title='ACID Properties', topic=topic).exists())

    def test_edit_entry(self):
        topic = Topic.objects.create(user=self.user, title='Operating Systems')
        entry = Entry.objects.create(topic=topic, title='Processes', content='Initial note')
        response = self.client.post(reverse('learning_logs:entry_edit', kwargs={'entry_id': entry.id}), {
            'title': 'Processes & Threads',
            'content': 'Processes have separate address space; threads share it.',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_detail', kwargs={'topic_id': topic.id}))
        entry.refresh_from_db()
        self.assertEqual(entry.title, 'Processes & Threads')
        self.assertEqual(entry.content, 'Processes have separate address space; threads share it.')

    def test_delete_entry(self):
        topic = Topic.objects.create(user=self.user, title='Networks')
        entry = Entry.objects.create(topic=topic, title='TCP Handshake', content='SYN, SYN-ACK, ACK')
        response = self.client.post(reverse('learning_logs:entry_delete', kwargs={'entry_id': entry.id}), follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_detail', kwargs={'topic_id': topic.id}))
        self.assertFalse(Entry.objects.filter(id=entry.id).exists())


class SearchAndDashboardTests(TestCase):
    """Test dashboard metrics and search functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='diana', password='Password123!')
        self.client.force_login(self.user)

        self.topic1 = Topic.objects.create(user=self.user, title='Python Basics', description='Intro to Python')
        self.topic2 = Topic.objects.create(user=self.user, title='Django Basics', description='Web development with Django')

        self.entry1 = Entry.objects.create(topic=self.topic1, title='Variables', content='Dynamic typing in Python')
        self.entry2 = Entry.objects.create(topic=self.topic2, title='ORM Queries', content='Filter, exclude, aggregate')

    def test_dashboard_metrics(self):
        response = self.client.get(reverse('learning_logs:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_topics'], 2)
        self.assertEqual(response.context['total_entries'], 2)
        self.assertContains(response, 'Python Basics')
        self.assertContains(response, 'Django Basics')

    def test_search_by_topic_title(self):
        response = self.client.get(reverse('learning_logs:search'), {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Basics')
        self.assertContains(response, 'Variables')

    def test_search_by_entry_content(self):
        response = self.client.get(reverse('learning_logs:search'), {'q': 'aggregate'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ORM Queries')

    def test_search_empty_results(self):
        response = self.client.get(reverse('learning_logs:search'), {'q': 'NonExistentKeywordXYZ'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Matching Results Found')

    def test_in_topic_search(self):
        # Search within topic1 for 'Variables'
        response = self.client.get(reverse('learning_logs:topic_detail', kwargs={'topic_id': self.topic1.id}), {'q': 'Variables'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Variables')

        # Search within topic1 for a query that only exists in topic2
        response_miss = self.client.get(reverse('learning_logs:topic_detail', kwargs={'topic_id': self.topic1.id}), {'q': 'aggregate'})
        self.assertEqual(response_miss.status_code, 200)
        self.assertNotContains(response_miss, 'ORM Queries')
        self.assertContains(response_miss, 'No Entries Found')


class FormValidationTests(TestCase):
    """Test ModelForms for topic and entry."""

    def test_topic_form_validation(self):
        form_valid = TopicForm(data={'title': 'React Fundamentals', 'description': 'Hooks & State'})
        self.assertTrue(form_valid.is_valid())

        form_invalid = TopicForm(data={'title': '', 'description': 'Missing title'})
        self.assertFalse(form_invalid.is_valid())
        self.assertIn('title', form_invalid.errors)

    def test_entry_form_validation(self):
        form_valid = EntryForm(data={'title': 'useEffect hook', 'content': 'Handles side effects'})
        self.assertTrue(form_valid.is_valid())

        form_invalid = EntryForm(data={'title': '', 'content': ''})
        self.assertFalse(form_invalid.is_valid())
        self.assertIn('title', form_invalid.errors)
        self.assertIn('content', form_invalid.errors)

    def test_add_entry_without_topics_redirects(self):
        user = User.objects.create_user(username='zerotopicuser', password='Password123!')
        client = Client()
        client.force_login(user)
        response = client.get(reverse('learning_logs:entry_create'), follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_create'))
        self.assertContains(response, 'You must create at least one topic before adding learning entries.')



from .models import Summary, Quiz, Question, Choice, QuizAttempt, ChatSession, ChatMessage
from . import ai_service
import unittest.mock as mock


class SummaryAndAISummarizerTests(TestCase):
    """Test AI note summarizer generation, model methods, and access control."""

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='alice_summary', password='Password123!')
        self.user_b = User.objects.create_user(username='bob_summary', password='Password123!')

        self.topic = Topic.objects.create(user=self.user_a, title='Cybersecurity Basics')
        self.entry = Entry.objects.create(
            topic=self.topic,
            title='Cross-Site Scripting (XSS)',
            content='Cross-Site Scripting is a client-side vulnerability where malicious scripts are injected into trusted websites. Input sanitization: always escape user input.'
        )

    def test_generate_summary_in_mock_mode(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('learning_logs:entry_summarize', kwargs={'entry_id': self.entry.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Executive Summary')
        self.assertContains(response, 'Demo / Mock AI Mode Active')

        # Check summary saved in DB
        summary = Summary.objects.get(entry=self.entry)
        self.assertEqual(summary.user, self.user_a)
        self.assertTrue(summary.is_mock)
        self.assertTrue(len(summary.get_points_list()) > 0)
        self.assertTrue(len(summary.get_terms_list()) > 0)

    def test_regenerate_summary(self):
        self.client.force_login(self.user_a)
        # First creation
        self.client.get(reverse('learning_logs:entry_summarize', kwargs={'entry_id': self.entry.id}))
        initial_count = Summary.objects.count()

        # Regenerate with flag
        response = self.client.get(reverse('learning_logs:entry_summarize', kwargs={'entry_id': self.entry.id}) + '?regenerate=1')
        self.assertEqual(response.status_code, 200)
        # Count should remain 1 because it updates the existing entry summary
        self.assertEqual(Summary.objects.count(), initial_count)

    def test_user_cannot_summarize_or_view_another_users_entry(self):
        """Bob cannot access or generate a summary for Alice's entry."""
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('learning_logs:entry_summarize', kwargs={'entry_id': self.entry.id}))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Summary.objects.filter(entry=self.entry).exists())

    def test_summary_list_view(self):
        Summary.objects.create(
            entry=self.entry,
            user=self.user_a,
            summary_text="Alice's Summary",
            key_points="• Point 1",
            key_terms="Term: Def",
            is_mock=True
        )
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('learning_logs:summary_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cross-Site Scripting (XSS)")

        # Bob should not see Alice's summary in Bob's list
        self.client.force_login(self.user_b)
        response_bob = self.client.get(reverse('learning_logs:summary_list'))
        self.assertNotContains(response_bob, "Cross-Site Scripting (XSS)")


class QuizAndScoringTests(TestCase):
    """Test AI quiz generation, attempt tracking, server-side grading, and tampering protection."""

    def setUp(self):
        self.client = Client()
        self.alice = User.objects.create_user(username='alice_quiz', password='Password123!')
        self.bob = User.objects.create_user(username='bob_quiz', password='Password123!')

        self.topic = Topic.objects.create(user=self.alice, title='Computer Networking')
        self.entry = Entry.objects.create(
            topic=self.topic,
            title='TCP vs UDP Protocol',
            content='TCP is a connection-oriented protocol that guarantees delivery via a 3-way handshake. UDP is connectionless and does not guarantee packet delivery.'
        )

    def test_generate_quiz_success(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse('learning_logs:quiz_generate', kwargs={'entry_id': self.entry.id}))
        self.assertEqual(response.status_code, 302)

        quiz = Quiz.objects.filter(entry=self.entry).first()
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.user, self.alice)
        self.assertTrue(quiz.questions.count() > 0)

        # Verify each question has choices and at least one is correct
        for question in quiz.questions.all():
            self.assertEqual(question.choices.count(), 4)
            self.assertTrue(question.choices.filter(is_correct=True).exists())

    def test_user_cannot_generate_quiz_on_another_users_entry(self):
        self.client.force_login(self.bob)
        response = self.client.get(reverse('learning_logs:quiz_generate', kwargs={'entry_id': self.entry.id}))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Quiz.objects.filter(entry=self.entry).exists())

    def test_user_cannot_take_another_users_quiz(self):
        quiz = Quiz.objects.create(entry=self.entry, user=self.alice, title='Alice Networking Quiz')
        self.client.force_login(self.bob)
        response = self.client.get(reverse('learning_logs:quiz_take', kwargs={'quiz_id': quiz.id}))
        self.assertEqual(response.status_code, 404)

    def test_server_side_scoring_calculation(self):
        quiz = Quiz.objects.create(entry=self.entry, user=self.alice, title='Scoring Test Quiz')
        q1 = Question.objects.create(quiz=quiz, text='What is TCP?', order=1)
        c1_correct = Choice.objects.create(question=q1, text='Connection oriented', is_correct=True, order=1)
        c1_wrong = Choice.objects.create(question=q1, text='Connectionless', is_correct=False, order=2)

        q2 = Question.objects.create(quiz=quiz, text='What is UDP?', order=2)
        c2_wrong = Choice.objects.create(question=q2, text='Guarantees delivery', is_correct=False, order=1)
        c2_correct = Choice.objects.create(question=q2, text='Connectionless unreliable', is_correct=True, order=2)

        self.client.force_login(self.alice)

        # Submit 1 correct and 1 incorrect answer
        post_data = {
            f'question_{q1.id}': str(c1_correct.id),
            f'question_{q2.id}': str(c2_wrong.id),
        }
        response = self.client.post(reverse('learning_logs:quiz_take', kwargs={'quiz_id': quiz.id}), post_data)
        self.assertEqual(response.status_code, 200)

        # Score must be exactly 1 out of 2 (50.0%)
        attempt = QuizAttempt.objects.filter(quiz=quiz, user=self.alice).first()
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.total_questions, 2)
        self.assertEqual(attempt.percentage, 50.0)
        self.assertContains(response, '1 / 2')
        self.assertContains(response, '50.0% Score')

    def test_client_side_score_tampering_prevented(self):
        """User submitting fake or non-existent choice IDs gets 0, cannot manipulate server score."""
        quiz = Quiz.objects.create(entry=self.entry, user=self.alice, title='Tamper Test')
        q1 = Question.objects.create(quiz=quiz, text='Tamper question?', order=1)
        Choice.objects.create(question=q1, text='Legit Choice', is_correct=True, order=1)

        self.client.force_login(self.alice)
        # Attempt to inject invalid choice ID
        response = self.client.post(reverse('learning_logs:quiz_take', kwargs={'quiz_id': quiz.id}), {
            f'question_{q1.id}': '9999999',
        })
        self.assertEqual(response.status_code, 200)
        attempt = QuizAttempt.objects.get(quiz=quiz, user=self.alice)
        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.percentage, 0.0)


class AskNotesChatbotTests(TestCase):
    """Test retrieval-augmented chatbot, user scoping, and prompt grounding."""

    def setUp(self):
        self.client = Client()
        self.alice = User.objects.create_user(username='alice_chat', password='Password123!')
        self.bob = User.objects.create_user(username='bob_chat', password='Password123!')

        self.topic_alice = Topic.objects.create(user=self.alice, title='Web Security')
        self.entry_alice = Entry.objects.create(
            topic=self.topic_alice,
            title='SQL Injection Secrets',
            content='SQL Injection happens when untrusted user input is directly concatenated into SQL queries. Prevention requires parameterized queries and prepared statements.'
        )

        self.topic_bob = Topic.objects.create(user=self.bob, title='Python Data Structures')
        self.entry_bob = Entry.objects.create(
            topic=self.topic_bob,
            title='Python Dictionaries',
            content='Python dictionaries use hash tables to achieve average O(1) key lookups and insertions.'
        )

    def test_alice_asks_about_her_own_note(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse('learning_logs:ask_notes'))
        self.assertEqual(response.status_code, 200)

        # Alice sends a query
        post_response = self.client.post(reverse('learning_logs:ask_notes'), {
            'query': 'Explain SQL Injection prevention',
        }, follow=True)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, 'SQL Injection Secrets')
        self.assertContains(post_response, 'parameterized queries')

    def test_bob_cannot_retrieve_alices_private_notes(self):
        """When Bob asks about SQL Injection, Alice's note must NOT be retrieved or leaked."""
        self.client.force_login(self.bob)
        post_response = self.client.post(reverse('learning_logs:ask_notes'), {
            'query': 'Tell me about SQL Injection Secrets',
        }, follow=True)
        self.assertEqual(post_response.status_code, 200)
        # Should not reveal Alice's secret content
        self.assertNotContains(post_response, 'parameterized queries and prepared statements')
        # Assistant must inform Bob that his notes don't contain this
        self.assertContains(post_response, 'none of them contain specific information answering')

    def test_bob_cannot_view_or_post_to_alices_chat_session(self):
        session_alice = ChatSession.objects.create(user=self.alice, title="Alice Private Session")
        self.client.force_login(self.bob)
        response = self.client.get(reverse('learning_logs:ask_notes_session', kwargs={'session_id': session_alice.id}))
        self.assertEqual(response.status_code, 404)

        # Bob cannot clear Alice's chat
        clear_response = self.client.get(reverse('learning_logs:chat_clear', kwargs={'session_id': session_alice.id}))
        self.assertEqual(clear_response.status_code, 404)

    def test_chat_clear_view(self):
        session = ChatSession.objects.create(user=self.alice, title="Session to clear")
        ChatMessage.objects.create(session=session, role='user', content='Hello')
        ChatMessage.objects.create(session=session, role='assistant', content='Hi')
        self.assertEqual(session.messages.count(), 2)

        self.client.force_login(self.alice)
        response = self.client.get(reverse('learning_logs:chat_clear', kwargs={'session_id': session.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(session.messages.count(), 0)


class AIServiceUnitTests(TestCase):
    """Test AI service functions, mock fallback, input sanitization, and error handling."""

    def test_sanitize_user_text(self):
        from .ai_service import sanitize_user_text
        text_with_null = "Hello\x00World"
        self.assertEqual(sanitize_user_text(text_with_null), "HelloWorld")

        long_text = "A" * 15000
        sanitized = sanitize_user_text(long_text, max_length=100)
        self.assertEqual(len(sanitized), 100)

    def test_mock_provider_empty_content(self):
        provider = ai_service.MockAIProvider()
        res = provider.summarize("Empty Note", "")
        self.assertTrue(res["is_mock"])
        self.assertIn("does not contain enough text", res["summary"])

    def test_mock_provider_quiz_generation_integrity(self):
        provider = ai_service.MockAIProvider()
        questions = provider.generate_quiz(
            "Operating Systems",
            "Virtual memory is a memory management capability of an operating system. Paging divides memory into fixed-size blocks.",
            num_questions=3
        )
        self.assertEqual(len(questions), 3)
        for q in questions:
            self.assertEqual(len(q["choices"]), 4)
            correct_count = sum(1 for c in q["choices"] if c["is_correct"])
            self.assertEqual(correct_count, 1)

    def test_external_provider_fallback_on_network_failure(self):
        """Verify OpenAICompatibleProvider falls back gracefully to Mock when API request fails."""
        provider = ai_service.OpenAICompatibleProvider(
            api_key="fake_key",
            model="fake_model",
            base_url="https://invalid.example.com"
        )
        with mock.patch.object(provider, '_call_chat_completion', side_effect=Exception("Connection timed out")):
            summary = provider.summarize("Network Protocols", "TCP uses a three-way handshake.")
            self.assertTrue(summary["is_mock"])
            self.assertIn("FALLBACK TO DEMO MODE", summary["summary"])


class DualLoginAndOTPAuthenticationTests(TestCase):
    """Test dual authentication (password & email OTP), cooldowns, lockouts, and edge cases."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='authuser',
            email='authuser@example.com',
            password='Password123!'
        )

    def test_login_with_username(self):
        response = self.client.post(reverse('learning_logs:login'), {
            'auth_method': 'password',
            'username': 'authuser',
            'password': 'Password123!',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:dashboard'))
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_with_email(self):
        response = self.client.post(reverse('learning_logs:login'), {
            'auth_method': 'password',
            'username': 'authuser@example.com',
            'password': 'Password123!',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:dashboard'))
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_with_incorrect_password(self):
        response = self.client.post(reverse('learning_logs:login'), {
            'auth_method': 'password',
            'username': 'authuser@example.com',
            'password': 'WrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_request_otp_for_registered_user(self):
        mail.outbox.clear()
        response = self.client.post(reverse('learning_logs:login'), {
            'auth_method': 'otp_request',
            'email': 'authuser@example.com',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:verify_otp'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your AI KnowledgeHub One-Time Verification Code", mail.outbox[0].subject)

        # Verify challenge exists in DB
        challenge = EmailOTP.objects.filter(email='authuser@example.com', is_used=False).first()
        self.assertIsNotNone(challenge)
        self.assertEqual(challenge.user, self.user)

    def test_request_otp_for_unregistered_email_generic_response(self):
        mail.outbox.clear()
        response = self.client.post(reverse('learning_logs:login'), {
            'auth_method': 'otp_request',
            'email': 'nonexistent@example.com',
        }, follow=True)
        # Prevents email enumeration: redirects identically to verify_otp
        self.assertRedirects(response, reverse('learning_logs:verify_otp'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(EmailOTP.objects.filter(email='nonexistent@example.com').exists())

    def test_verify_otp_success(self):
        challenge, raw_otp = EmailOTP.create_challenge(email='authuser@example.com', user=self.user)
        session = self.client.session
        session['otp_email'] = 'authuser@example.com'
        session.save()

        response = self.client.post(reverse('learning_logs:verify_otp'), {
            'otp': raw_otp,
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:dashboard'))
        self.assertTrue(response.context['user'].is_authenticated)

        challenge.refresh_from_db()
        self.assertTrue(challenge.is_used)

    def test_verify_otp_invalid_code(self):
        challenge, raw_otp = EmailOTP.create_challenge(email='authuser@example.com', user=self.user)
        session = self.client.session
        session['otp_email'] = 'authuser@example.com'
        session.save()

        response = self.client.post(reverse('learning_logs:verify_otp'), {
            'otp': '999999' if raw_otp != '999999' else '888888',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        challenge.refresh_from_db()
        self.assertEqual(challenge.attempts, 1)
        self.assertFalse(challenge.is_used)

    def test_verify_otp_expired(self):
        challenge, raw_otp = EmailOTP.create_challenge(email='authuser@example.com', user=self.user)
        challenge.expires_at = timezone.now() - timedelta(minutes=1)
        challenge.save()

        session = self.client.session
        session['otp_email'] = 'authuser@example.com'
        session.save()

        response = self.client.post(reverse('learning_logs:verify_otp'), {
            'otp': raw_otp,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_verify_otp_reuse_prevention(self):
        challenge, raw_otp = EmailOTP.create_challenge(email='authuser@example.com', user=self.user)
        session = self.client.session
        session['otp_email'] = 'authuser@example.com'
        session.save()

        # First verification succeeds
        response1 = self.client.post(reverse('learning_logs:verify_otp'), {'otp': raw_otp}, follow=True)
        self.assertRedirects(response1, reverse('learning_logs:dashboard'))
        self.client.logout()

        # Second verification attempt with same OTP fails
        session = self.client.session
        session['otp_email'] = 'authuser@example.com'
        session.save()
        response2 = self.client.post(reverse('learning_logs:verify_otp'), {'otp': raw_otp}, follow=True)
        self.assertFalse(response2.context['user'].is_authenticated)

    def test_verify_otp_lockout_after_max_attempts(self):
        challenge, raw_otp = EmailOTP.create_challenge(email='authuser@example.com', user=self.user)
        session = self.client.session
        session['otp_email'] = 'authuser@example.com'
        session.save()

        # Fail 5 times
        for _ in range(5):
            self.client.post(reverse('learning_logs:verify_otp'), {'otp': '000000'})
        challenge.refresh_from_db()
        self.assertTrue(challenge.is_locked())

        # 6th attempt with correct OTP must fail due to lockout
        response = self.client.post(reverse('learning_logs:verify_otp'), {'otp': raw_otp})
        self.assertFalse(response.context['user'].is_authenticated)

    def test_resend_otp_cooldown(self):
        challenge, _ = EmailOTP.create_challenge(email='authuser@example.com', user=self.user)
        session = self.client.session
        session['otp_email'] = 'authuser@example.com'
        session.save()

        response = self.client.get(reverse('learning_logs:resend_otp'), follow=True)
        self.assertRedirects(response, reverse('learning_logs:verify_otp'))
        # No new challenge should be created because cooldown is active
        self.assertEqual(EmailOTP.objects.filter(email='authuser@example.com').count(), 1)

    def test_resend_otp_without_session_redirects_to_login(self):
        response = self.client.get(reverse('learning_logs:resend_otp'))
        self.assertRedirects(response, reverse('learning_logs:login'))

    def test_verify_otp_without_session_redirects_to_login(self):
        response = self.client.get(reverse('learning_logs:verify_otp'))
        self.assertRedirects(response, reverse('learning_logs:login'))


class PasswordResetWorkflowTests(TestCase):
    """Test full password reset workflow: form, email token generation, confirmation, and update."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='resetuser',
            email='resetuser@example.com',
            password='OldPassword123!'
        )

    def test_password_reset_form_render(self):
        response = self.client.get(reverse('learning_logs:password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')

    def test_password_reset_post_sends_email_with_token(self):
        mail.outbox.clear()
        response = self.client.post(reverse('learning_logs:password_reset'), {
            'email': 'resetuser@example.com',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset your AI KnowledgeHub password", mail.outbox[0].subject)
        self.assertIn("/reset/", mail.outbox[0].body)

    def test_password_reset_post_unknown_email_shows_done_page(self):
        mail.outbox.clear()
        response = self.client.post(reverse('learning_logs:password_reset'), {
            'email': 'ghost@example.com',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_and_complete(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        confirm_url = reverse('learning_logs:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

        # GET confirm page (follows internal security redirect to set-password/)
        response = self.client.get(confirm_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_confirm.html')
        set_password_url = response.redirect_chain[0][0]

        # POST new password to set_password_url
        post_response = self.client.post(set_password_url, {
            'new_password1': 'NewSecurePass123!',
            'new_password2': 'NewSecurePass123!',
        }, follow=True)
        self.assertRedirects(post_response, reverse('learning_logs:password_reset_complete'))

        # Verify login with new password succeeds
        login_response = self.client.post(reverse('learning_logs:login'), {
            'auth_method': 'password',
            'username': 'resetuser',
            'password': 'NewSecurePass123!',
        }, follow=True)
        self.assertTrue(login_response.context['user'].is_authenticated)

    def test_password_reset_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = 'invalid-token-123'
        confirm_url = reverse('learning_logs:password_reset_confirm', kwargs={'uidb64': uid, 'token': invalid_token})
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password Reset Link Invalid")


class DocumentAssistantAndTextImproverTests(TestCase):
    """Automated tests for AI Document Studio, user-provided text Q&A, and text improvement."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='docuser',
            email='docuser@example.com',
            password='DocPassword123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='OtherPassword123!'
        )
        self.topic = Topic.objects.create(
            user=self.user,
            title='Machine Learning Notes',
            description='Supervised and unsupervised learning.'
        )
        self.entry = Entry.objects.create(
            topic=self.topic,
            title='Gradient Descent Basics',
            content='Gradient descent is an optimization algorithm used to minimize cost functions by iteratively moving in the direction of steepest descent.'
        )
        self.other_topic = Topic.objects.create(
            user=self.other_user,
            title='Secret Research',
            description='Not for docuser'
        )
        self.other_entry = Entry.objects.create(
            topic=self.other_topic,
            title='Confidential Note',
            content='Secret details that docuser must never access.'
        )
        self.client.force_login(self.user)

    def test_document_assistant_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('learning_logs:document_assistant'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('learning_logs:login'), response.url)

    def test_document_assistant_get_page(self):
        response = self.client.get(reverse('learning_logs:document_assistant'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_logs/document_assistant.html')
        self.assertIn('form', response.context)

    def test_document_assistant_preload_saved_note(self):
        url = f"{reverse('learning_logs:document_assistant')}?note_id={self.entry.id}&task=improve"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['preloaded_entry'], self.entry)
        self.assertEqual(response.context['form'].initial['document_text'], self.entry.content)

    def test_document_assistant_summarize_user_provided_text(self):
        user_text = (
            "Convolutional neural networks apply kernel filters over feature maps. "
            "Pooling layers downsample spatial representations. "
            "Dense classification layers output final softmax probabilities."
        )
        response = self.client.post(reverse('learning_logs:document_assistant'), {
            'action_type': 'analyze',
            'document_text': user_text,
            'task': 'summarize',
        })
        self.assertEqual(response.status_code, 200)
        result_data = response.context['result_data']
        self.assertIsNotNone(result_data)
        self.assertEqual(result_data['task'], 'summarize')
        self.assertTrue(len(result_data['result']) > 0)

    def test_document_assistant_key_points_task(self):
        user_text = (
            "First concept: overfitting happens when model memorizes training noise. "
            "Second concept: regularization penalizes large weight magnitudes. "
            "Third concept: cross validation validates generalization accuracy."
        )
        response = self.client.post(reverse('learning_logs:document_assistant'), {
            'action_type': 'analyze',
            'document_text': user_text,
            'task': 'key_points',
        })
        self.assertEqual(response.status_code, 200)
        result_data = response.context['result_data']
        self.assertEqual(result_data['task'], 'key_points')
        self.assertTrue(len(result_data['key_points']) >= 2)

    def test_document_assistant_improve_task(self):
        raw_text = "u should check ur hyperparameters w/ cross validation."
        response = self.client.post(reverse('learning_logs:document_assistant'), {
            'action_type': 'analyze',
            'document_text': raw_text,
            'task': 'improve',
        })
        self.assertEqual(response.status_code, 200)
        result_data = response.context['result_data']
        self.assertEqual(result_data['task'], 'improve')
        self.assertIn('you should check your hyperparameters with', result_data['result'].lower())

    def test_document_assistant_qa_task_matched(self):
        doc_text = "Support Vector Machines seek an optimal hyperplane with maximal margin between classes."
        response = self.client.post(reverse('learning_logs:document_assistant'), {
            'action_type': 'analyze',
            'document_text': doc_text,
            'task': 'qa',
            'question': 'What do support vector machines seek?',
        })
        self.assertEqual(response.status_code, 200)
        result_data = response.context['result_data']
        self.assertEqual(result_data['task'], 'qa')
        self.assertIn("optimal hyperplane", result_data['result'])

    def test_document_assistant_qa_task_unmatched(self):
        doc_text = "Python lists are mutable dynamic arrays implemented in C."
        response = self.client.post(reverse('learning_logs:document_assistant'), {
            'action_type': 'analyze',
            'document_text': doc_text,
            'task': 'qa',
            'question': 'What is quantum teleportation?',
        })
        self.assertEqual(response.status_code, 200)
        result_data = response.context['result_data']
        self.assertIn("no relevant information was found", result_data['result'])

    def test_document_assistant_save_as_note_success(self):
        response = self.client.post(reverse('learning_logs:document_assistant'), {
            'action_type': 'save_note',
            'topic_id': self.topic.id,
            'note_title': 'Saved AI Summary',
            'note_content': 'Key points from AI Document Studio analysis.',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_detail', kwargs={'topic_id': self.topic.id}))
        new_entry = Entry.objects.filter(title='Saved AI Summary', topic=self.topic).first()
        self.assertIsNotNone(new_entry)
        self.assertEqual(new_entry.content, 'Key points from AI Document Studio analysis.')

    def test_document_assistant_save_as_note_cross_user_denied(self):
        response = self.client.post(reverse('learning_logs:document_assistant'), {
            'action_type': 'save_note',
            'topic_id': self.other_topic.id,
            'note_title': 'Intruder Note',
            'note_content': 'Should fail',
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Entry.objects.filter(title='Intruder Note').exists())

    def test_entry_improve_view_get(self):
        url = reverse('learning_logs:entry_improve', kwargs={'entry_id': self.entry.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_logs/entry_improve.html')
        self.assertIn('improved_result', response.context)
        self.assertEqual(response.context['entry'], self.entry)

    def test_entry_improve_view_apply_changes(self):
        url = reverse('learning_logs:entry_improve', kwargs={'entry_id': self.entry.id})
        response = self.client.post(url, {
            'action': 'apply',
            'improved_content': 'Refined and perfected gradient descent notes.',
        }, follow=True)
        self.assertRedirects(response, reverse('learning_logs:topic_detail', kwargs={'topic_id': self.topic.id}))
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.content, 'Refined and perfected gradient descent notes.')

    def test_entry_improve_cross_user_forbidden(self):
        url = reverse('learning_logs:entry_improve', kwargs={'entry_id': self.other_entry.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_ai_status_helper(self):
        status = ai_service.get_ai_service_status()
        self.assertIn('provider', status)
        self.assertIn('is_live', status)
        self.assertIn('message', status)
        self.assertIsInstance(status['is_live'], bool)

    def test_dev_otp_banner_output(self):
        from .views import print_dev_otp_banner
        print_dev_otp_banner('test@example.com', '123456', 'testuser')

