from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Avg
from .models import (
    Topic, Entry, Summary, Quiz, Question, Choice,
    QuizAttempt, ChatSession, ChatMessage
)
from .forms import UserRegistrationForm, TopicForm, EntryForm, QuickEntryForm
from . import ai_service


# ===========================================================================
# Authentication & Landing Views
# ===========================================================================

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
    """User logout view supporting both POST and GET."""
    if request.method in ['POST', 'GET']:
        logout(request)
        messages.info(request, "You have been logged out successfully. Have a productive day!")
        return redirect('learning_logs:login')


# ===========================================================================
# Dashboard & Analytics Views
# ===========================================================================

@login_required
def dashboard_view(request):
    """User dashboard summarizing learning statistics, recent topics, notes, and quizzes."""
    user = request.user
    user_topics = Topic.objects.filter(user=user)
    user_entries = Entry.objects.filter(topic__user=user)
    user_attempts = QuizAttempt.objects.filter(user=user)

    total_topics = user_topics.count()
    total_entries = user_entries.count()
    total_quizzes_attempted = user_attempts.count()

    avg_score_data = user_attempts.aggregate(Avg('percentage'))
    avg_score = round(avg_score_data['percentage__avg'] or 0.0, 1)

    recent_topics = user_topics.order_by('-updated_at')[:5]
    recent_entries = user_entries.select_related('topic').order_by('-created_at')[:5]
    recent_attempts = user_attempts.select_related('quiz', 'quiz__entry').order_by('-attempted_at')[:5]
    recent_summaries = Summary.objects.filter(user=user).select_related('entry')[:4]

    context = {
        'total_topics': total_topics,
        'total_entries': total_entries,
        'total_quizzes_attempted': total_quizzes_attempted,
        'avg_score': avg_score,
        'recent_topics': recent_topics,
        'recent_entries': recent_entries,
        'recent_attempts': recent_attempts,
        'recent_summaries': recent_summaries,
    }
    return render(request, 'learning_logs/dashboard.html', context)


# ===========================================================================
# Topic CRUD Views
# ===========================================================================

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


# ===========================================================================
# Learning Entry CRUD Views
# ===========================================================================

@login_required
def entry_list_view(request):
    """Browse all entries belonging to the current user with topic filter."""
    user_entries = Entry.objects.filter(topic__user=request.user).select_related('topic').order_by('-created_at')
    topics = Topic.objects.filter(user=request.user).order_by('title')

    selected_topic_id = request.GET.get('topic')
    if selected_topic_id:
        user_entries = user_entries.filter(topic_id=selected_topic_id)

    query = request.GET.get('q', '').strip()
    if query:
        user_entries = user_entries.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    context = {
        'entries': user_entries,
        'topics': topics,
        'selected_topic_id': selected_topic_id,
        'query': query,
    }
    return render(request, 'learning_logs/entry_list.html', context)


@login_required
def entry_create_view(request, topic_id=None):
    """Add a new learning entry under a specific topic or via quick action."""
    topic = None
    if topic_id:
        topic = get_object_or_404(Topic, id=topic_id, user=request.user)

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


# ===========================================================================
# AI Feature One: Intelligent Notes Summarizer
# ===========================================================================

@login_required
def entry_summarize_view(request, entry_id):
    """
    Generate or view an AI summary for a specific note.
    Saves the summary so users can revisit it without wasting API quota.
    """
    entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)
    regenerate = request.GET.get('regenerate') == '1'

    summary = Summary.objects.filter(entry=entry, user=request.user).first()

    if not summary or regenerate:
        ai_result = ai_service.summarize_note(entry.title, entry.content)
        summary_text = ai_result.get('summary', '')
        key_points = "\n".join(ai_result.get('key_points', []))
        key_terms = "\n".join(ai_result.get('key_terms', []))
        is_mock = ai_result.get('is_mock', True)

        if summary and regenerate:
            summary.summary_text = summary_text
            summary.key_points = key_points
            summary.key_terms = key_terms
            summary.is_mock = is_mock
            summary.save()
            messages.success(request, "Summary regenerated successfully!")
        else:
            summary = Summary.objects.create(
                entry=entry,
                user=request.user,
                summary_text=summary_text,
                key_points=key_points,
                key_terms=key_terms,
                is_mock=is_mock
            )
            messages.success(request, "AI summary generated successfully!")

    context = {
        'entry': entry,
        'summary': summary,
        'key_points_list': summary.get_points_list(),
        'key_terms_list': summary.get_terms_list(),
    }
    return render(request, 'learning_logs/summary_detail.html', context)


@login_required
def summary_list_view(request):
    """Display all summaries saved by the authenticated user."""
    summaries = Summary.objects.filter(user=request.user).select_related('entry', 'entry__topic').order_by('-created_at')
    return render(request, 'learning_logs/summary_list.html', {'summaries': summaries})


# ===========================================================================
# AI Feature Two: AI Quiz Generator & Scoring
# ===========================================================================

@login_required
def quiz_generate_view(request, entry_id):
    """
    Generate a multiple-choice quiz for the selected learning entry using AI.
    Saves questions and choices in the database and redirects to the quiz interface.
    """
    entry = get_object_or_404(Entry, id=entry_id, topic__user=request.user)

    # Optional number of questions (default: 5)
    num_questions = int(request.GET.get('n', 5))
    num_questions = max(1, min(num_questions, 10))

    try:
        raw_quiz = ai_service.generate_quiz(entry.title, entry.content, num_questions=num_questions)
        if not raw_quiz:
            messages.error(request, "Could not generate questions for this note. Ensure the note has adequate text.")
            return redirect('learning_logs:topic_detail', topic_id=entry.topic.id)

        with transaction.atomic():
            quiz = Quiz.objects.create(
                entry=entry,
                user=request.user,
                title=f"Quiz: {entry.title}",
                is_mock=getattr(ai_service.get_ai_service(), 'mock_fallback', None) is None
            )

            for q_idx, q_data in enumerate(raw_quiz, start=1):
                question = Question.objects.create(
                    quiz=quiz,
                    text=q_data.get('question', f"Question {q_idx}"),
                    explanation=q_data.get('explanation', ''),
                    order=q_idx
                )
                choices_data = q_data.get('choices', [])
                for c_idx, c_data in enumerate(choices_data, start=1):
                    Choice.objects.create(
                        question=question,
                        text=c_data.get('text', f"Option {c_idx}"),
                        is_correct=bool(c_data.get('is_correct', False)),
                        order=c_idx
                    )

        messages.success(request, f"New quiz generated for '{entry.title}' with {quiz.question_count} questions!")
        return redirect('learning_logs:quiz_take', quiz_id=quiz.id)

    except Exception as e:
        messages.error(request, f"Failed to generate quiz: {str(e)}")
        return redirect('learning_logs:topic_detail', topic_id=entry.topic.id)


@login_required
def quiz_take_view(request, quiz_id):
    """
    Display quiz to the user and handle submission.
    Calculates scores on the server side; client never receives answer keys in inputs.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    questions = quiz.questions.prefetch_related('choices').all()

    if request.method == 'POST':
        # Grade quiz on server-side
        total_questions = questions.count()
        if total_questions == 0:
            messages.warning(request, "This quiz contains no questions.")
            return redirect('learning_logs:quiz_history')

        score = 0
        graded_questions = []

        for q in questions:
            choice_key = f"question_{q.id}"
            selected_choice_id = request.POST.get(choice_key)
            selected_choice = None
            correct_choice = q.choices.filter(is_correct=True).first()

            is_user_correct = False
            if selected_choice_id:
                try:
                    selected_choice = q.choices.get(id=int(selected_choice_id))
                    if selected_choice.is_correct:
                        score += 1
                        is_user_correct = True
                except (Choice.DoesNotExist, ValueError):
                    pass

            graded_questions.append({
                'question': q,
                'selected_choice': selected_choice,
                'correct_choice': correct_choice,
                'is_correct': is_user_correct,
                'explanation': q.explanation,
            })

        percentage = round((score / total_questions) * 100, 1)

        # Save Quiz Attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user,
            score=score,
            total_questions=total_questions,
            percentage=percentage
        )

        context = {
            'quiz': quiz,
            'attempt': attempt,
            'score': score,
            'total_questions': total_questions,
            'percentage': percentage,
            'graded_questions': graded_questions,
        }
        return render(request, 'learning_logs/quiz_result.html', context)

    return render(request, 'learning_logs/quiz_take.html', {
        'quiz': quiz,
        'questions': questions,
    })


@login_required
def quiz_history_view(request):
    """Review past quiz attempts and scores for the current user."""
    attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz', 'quiz__entry', 'quiz__entry__topic').order_by('-attempted_at')
    user_quizzes = Quiz.objects.filter(user=request.user).select_related('entry', 'entry__topic').order_by('-created_at')

    context = {
        'attempts': attempts,
        'quizzes': user_quizzes,
    }
    return render(request, 'learning_logs/quiz_history.html', context)


# ===========================================================================
# AI Feature Three: Ask My Notes Chatbot
# ===========================================================================

@login_required
def ask_notes_view(request, session_id=None):
    """
    Ask questions strictly against the authenticated user's personal notes.
    Implements database-backed keyword retrieval scoped strictly to user's notes.
    """
    user = request.user

    # Fetch or create the active chat session
    if session_id:
        chat_session = get_object_or_404(ChatSession, id=session_id, user=user)
    else:
        chat_session = ChatSession.objects.filter(user=user).order_by('-updated_at').first()
        if not chat_session:
            chat_session = ChatSession.objects.create(user=user, title="Learning Q&A Session")

    all_sessions = ChatSession.objects.filter(user=user).order_by('-updated_at')
    messages_list = chat_session.messages.all().order_by('created_at')

    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if query:
            # 1. User-scoped keyword retrieval across notes
            query_words = [w.lower() for w in query.split() if len(w) > 2]
            user_entries = Entry.objects.filter(topic__user=user)

            matching_entries = []
            if query_words:
                # Rank entries by occurrences
                for entry in user_entries:
                    full_text = f"{entry.title} {entry.content}".lower()
                    score = sum(full_text.count(word) for word in query_words)
                    if score > 0:
                        matching_entries.append((score, entry))

                matching_entries.sort(key=lambda x: x[0], reverse=True)

            top_notes = [e for score, e in matching_entries[:4]]
            if not top_notes and user_entries.exists():
                # Provide top 2 recent notes as general fallback context
                top_notes = list(user_entries.order_by('-created_at')[:2])

            context_notes = [
                {
                    'topic': entry.topic.title,
                    'title': entry.title,
                    'content': entry.content
                }
                for entry in top_notes
            ]

            # 2. Call AI service with scoped reference notes
            answer = ai_service.answer_from_notes(query, context_notes)

            # 3. Save Chat History
            source_titles = ", ".join([n['title'] for n in context_notes]) if context_notes else "None"
            ChatMessage.objects.create(session=chat_session, role='user', content=query)
            ChatMessage.objects.create(
                session=chat_session,
                role='assistant',
                content=answer,
                retrieved_notes=source_titles
            )

            # Auto-title session after first message
            if chat_session.title == "Learning Q&A Session" and chat_session.messages.count() <= 2:
                chat_session.title = query[:40] + ("..." if len(query) > 40 else "")
                chat_session.save()

            return redirect('learning_logs:ask_notes_session', session_id=chat_session.id)

    context = {
        'chat_session': chat_session,
        'all_sessions': all_sessions,
        'messages': messages_list,
        'has_notes': Entry.objects.filter(topic__user=user).exists(),
    }
    return render(request, 'learning_logs/ask_notes.html', context)


@login_required
def chat_new_view(request):
    """Start a fresh chat session for Ask My Notes."""
    session = ChatSession.objects.create(user=request.user, title="New Learning Q&A")
    return redirect('learning_logs:ask_notes_session', session_id=session.id)


@login_required
def chat_clear_view(request, session_id):
    """Clear all messages from the specified chat session."""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.messages.all().delete()
    messages.info(request, "Chat history has been cleared.")
    return redirect('learning_logs:ask_notes_session', session_id=session.id)


# ===========================================================================
# Search View
# ===========================================================================

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
