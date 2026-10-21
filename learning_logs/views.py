from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Topic, Entry
from .forms import UserRegistrationForm, TopicForm, EntryForm, QuickEntryForm


def index_view(request):
    """Public home/landing page or redirect to dashboard if authenticated."""
    if request.user.is_authenticated:
        return redirect('learning_logs:dashboard')
    return render(request, 'learning_logs/index.html')


def register_view(request):
    """User registration view with validation and auto-login upon success."""
    if request.user.is_authenticated:
        return redirect('learning_logs:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Personal Knowledge System, {user.username}! Your account has been created.")
            return redirect('learning_logs:dashboard')
        else:
            messages.error(request, "Please correct the errors below to complete your registration.")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """User login view with validation and feedback."""
    if request.user.is_authenticated:
        return redirect('learning_logs:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or 'learning_logs:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm(request)

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """User logout view supporting both POST and GET for smooth user experience."""
    if request.method in ['POST', 'GET']:
        logout(request)
        messages.info(request, "You have been logged out successfully. Have a productive day!")
        return redirect('learning_logs:login')


@login_required
def dashboard_view(request):
    """User dashboard summarizing statistics, recent topics, and entries."""
    user = request.user
    user_topics = Topic.objects.filter(user=user)
    user_entries = Entry.objects.filter(topic__user=user)

    total_topics = user_topics.count()
    total_entries = user_entries.count()

    recent_topics = user_topics.order_by('-updated_at')[:5]
    recent_entries = user_entries.select_related('topic').order_by('-created_at')[:5]

    context = {
        'total_topics': total_topics,
        'total_entries': total_entries,
        'recent_topics': recent_topics,
        'recent_entries': recent_entries,
    }
    return render(request, 'learning_logs/dashboard.html', context)


@login_required
def topic_list_view(request):
    """List all topics owned by the current user."""
    topics = Topic.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'learning_logs/topic_list.html', {'topics': topics})


@login_required
def topic_detail_view(request, topic_id):
    """Show details of a specific topic and its entries, owned by current user."""
    topic = get_object_or_404(Topic, id=topic_id, user=request.user)
    entries = topic.entries.all().order_by('-created_at')

    # Optional within-topic search filter
    query = request.GET.get('q', '').strip()
    if query:
        entries = entries.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    context = {
        'topic': topic,
        'entries': entries,
        'query': query,
    }
    return render(request, 'learning_logs/topic_detail.html', context)


@login_required
def topic_create_view(request):
    """Create a new topic for the current user."""
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.user = request.user
            topic.save()
            messages.success(request, f"Topic '{topic.title}' was created successfully!")
            return redirect('learning_logs:topic_detail', topic_id=topic.id)
        else:
            messages.error(request, "Please correct the errors in the topic form.")
    else:
        form = TopicForm()

    return render(request, 'learning_logs/topic_form.html', {
        'form': form,
        'title': 'Create New Topic',
        'is_edit': False,
    })


@login_required
def topic_edit_view(request, topic_id):
    """Edit an existing topic owned by the current user."""
    topic = get_object_or_404(Topic, id=topic_id, user=request.user)

    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, f"Topic '{topic.title}' was updated successfully!")
            return redirect('learning_logs:topic_detail', topic_id=topic.id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = TopicForm(instance=topic)

    return render(request, 'learning_logs/topic_form.html', {
        'form': form,
        'topic': topic,
        'title': f'Edit Topic: {topic.title}',
        'is_edit': True,
    })


@login_required
def topic_delete_view(request, topic_id):
    """Delete an existing topic after user confirmation."""
    topic = get_object_or_404(Topic, id=topic_id, user=request.user)

    if request.method == 'POST':
        topic_title = topic.title
        topic.delete()
        messages.success(request, f"Topic '{topic_title}' and all its entries were deleted successfully.")
        return redirect('learning_logs:topic_list')

    return render(request, 'learning_logs/topic_confirm_delete.html', {'topic': topic})


@login_required
def entry_create_view(request, topic_id=None):
    """Add a new learning entry under a specific topic or via quick action."""
    topic = None
    if topic_id:
        topic = get_object_or_404(Topic, id=topic_id, user=request.user)

    # Check if user has any topics when using global add entry
    user_topics_count = Topic.objects.filter(user=request.user).count()
    if user_topics_count == 0:
        messages.warning(request, "You must create at least one topic before adding learning entries.")
        return redirect('learning_logs:topic_create')

    if request.method == 'POST':
        if topic:
            form = EntryForm(request.POST)
            if form.is_valid():
                entry = form.save(commit=False)
                entry.topic = topic
                entry.save()
                messages.success(request, f"Entry '{entry.title}' was added to '{topic.title}'!")
                return redirect('learning_logs:topic_detail', topic_id=topic.id)
        else:
            form = QuickEntryForm(request.POST, user=request.user)
            if form.is_valid():
                entry = form.save()
                messages.success(request, f"Entry '{entry.title}' was added to '{entry.topic.title}'!")
                return redirect('learning_logs:topic_detail', topic_id=entry.topic.id)

        messages.error(request, "Please correct the errors in the entry form.")
    else:
        if topic:
            form = EntryForm()
        else:
            form = QuickEntryForm(user=request.user)

    return render(request, 'learning_logs/entry_form.html', {
        'form': form,
        'topic': topic,
        'title': f"Add Entry to '{topic.title}'" if topic else "Add New Learning Entry",
        'is_edit': False,
    })


@login_required
def entry_edit_view(request, entry_id):
    """Edit an existing learning entry owned by current user."""
    entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)

    if request.method == 'POST':
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f"Entry '{entry.title}' was updated successfully!")
            return redirect('learning_logs:topic_detail', topic_id=entry.topic.id)
        else:
            messages.error(request, "Please correct the errors in the entry form.")
    else:
        form = EntryForm(instance=entry)

    return render(request, 'learning_logs/entry_form.html', {
        'form': form,
        'entry': entry,
        'topic': entry.topic,
        'title': f"Edit Entry: {entry.title}",
        'is_edit': True,
    })


@login_required
def entry_delete_view(request, entry_id):
    """Delete an existing learning entry after user confirmation."""
    entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)
    topic_id = entry.topic.id
    entry_title = entry.title

    if request.method == 'POST':
        entry.delete()
        messages.success(request, f"Entry '{entry_title}' was deleted successfully.")
        return redirect('learning_logs:topic_detail', topic_id=topic_id)

    return render(request, 'learning_logs/entry_confirm_delete.html', {
        'entry': entry,
        'topic': entry.topic,
    })


@login_required
def search_view(request):
    """Search user's topics and entries by keyword."""
    query = request.GET.get('q', '').strip()
    matching_topics = Topic.objects.none()
    matching_entries = Entry.objects.none()

    if query:
        matching_topics = Topic.objects.filter(
            user=request.user
        ).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()

        matching_entries = Entry.objects.filter(
            topic__user=request.user
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('topic').distinct()

    total_results = matching_topics.count() + matching_entries.count()

    context = {
        'query': query,
        'matching_topics': matching_topics,
        'matching_entries': matching_entries,
        'total_results': total_results,
    }
    return render(request, 'learning_logs/search_results.html', context)
