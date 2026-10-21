from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Topic, Entry
from .forms import TopicForm, EntryForm, UserRegistrationForm


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

