from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'learning_logs'

urlpatterns = [
    # Landing & Dashboard
    path('', views.index_view, name='index'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Dual Authentication (Password & Email OTP)
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),

    # Password Reset Workflow
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('learning_logs:password_reset_done')
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('learning_logs:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

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

    # AI Feature 1: Intelligent Notes Summarizer & Improver
    path('entries/<int:entry_id>/summarize/', views.entry_summarize_view, name='entry_summarize'),
    path('entries/<int:entry_id>/improve/', views.entry_improve_view, name='entry_improve'),
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

    # AI Feature 4: AI Document & Text Assistant Studio
    path('document-assistant/', views.document_assistant_view, name='document_assistant'),

    # Global Search
    path('search/', views.search_view, name='search'),
]
