from django.urls import path
from . import views

app_name = 'learning_logs'

urlpatterns = [
    # Landing & Dashboard
    path('', views.index_view, name='index'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Topics
    path('topics/', views.topic_list_view, name='topic_list'),
    path('topics/new/', views.topic_create_view, name='topic_create'),
    path('topics/<int:topic_id>/', views.topic_detail_view, name='topic_detail'),
    path('topics/<int:topic_id>/edit/', views.topic_edit_view, name='topic_edit'),
    path('topics/<int:topic_id>/delete/', views.topic_delete_view, name='topic_delete'),

    # Entries / Notes
    path('entries/', views.entry_list_view, name='entry_list'),
    path('topics/<int:topic_id>/entries/new/', views.entry_create_view, name='topic_entry_create'),
    path('entries/new/', views.entry_create_view, name='entry_create'),
    path('entries/<int:entry_id>/edit/', views.entry_edit_view, name='entry_edit'),
    path('entries/<int:entry_id>/delete/', views.entry_delete_view, name='entry_delete'),

    # AI Feature 1: Intelligent Notes Summarizer
    path('entries/<int:entry_id>/summarize/', views.entry_summarize_view, name='entry_summarize'),
    path('summaries/', views.summary_list_view, name='summary_list'),

    # AI Feature 2: AI Quiz Generator & Attempts
    path('entries/<int:entry_id>/quiz/generate/', views.quiz_generate_view, name='quiz_generate'),
    path('quizzes/<int:quiz_id>/', views.quiz_take_view, name='quiz_take'),
    path('quizzes/history/', views.quiz_history_view, name='quiz_history'),

    # AI Feature 3: Ask My Notes Chatbot
    path('ask-notes/', views.ask_notes_view, name='ask_notes'),
    path('ask-notes/<int:session_id>/', views.ask_notes_view, name='ask_notes_session'),
    path('ask-notes/new/', views.chat_new_view, name='chat_new'),
    path('ask-notes/<int:session_id>/clear/', views.chat_clear_view, name='chat_clear'),

    # Global Search
    path('search/', views.search_view, name='search'),
]
